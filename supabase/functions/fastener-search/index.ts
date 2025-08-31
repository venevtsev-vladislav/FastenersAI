import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type"
};

// ---------- utils ----------
function escapeSqlLike(v) {
  return (v || "").replace(/[%_\\]/g, "\\$&");
}

function normalizeStr(s) {
  if (!s) return "";
  return s.toLowerCase().trim()
    .replace(/м/g, "m") // кириллическая м -> m
    .replace(/[×хx]/g, "x") // ×/х/x -> x
    .replace(/\s+/g, " ")
    .replace(/din\s*([0-9]+)/g, (_m, p1) => `din${p1}`)
    .replace(/оцинк[а-я]*/g, "цинк");
}

function canonDiameter(d) {
  return d ? d.replace(/\s*мм$/i, "").toUpperCase().replace(/^М/, "M") : "";
}

function canonLength(l) {
  return l ? l.replace(/\s*мм$/i, "") : "";
}

function mxlVariants(d, l) {
  const D = canonDiameter(d), L = canonLength(l);
  if (!D || !L) return [];
  
  const dLat = D, dCyr = D.replace(/^M/, "М");
  const xs = ["x", "х", "×", "-"];
  const out = [];
  
  for (const X of xs) {
    out.push(`${dLat}${X}${L}`, `${dLat} ${X} ${L}`, `${dCyr}${X}${L}`, `${dCyr} ${X} ${L}`);
  }
  out.push(`${dLat}${L}`, `${dCyr}${L}`);
  
  return Array.from(new Set(out));
}

// Расширенный список негативных типов
const NEGATIVE_TYPES = [
  "гайк", "шайб", "саморез", "дюбел", "штанг", "шпил", "анкер", "дюбель",
  "шуруп", "анкер", "крюк", "блок", "вертлюг", "трос"
];

// Простая мягкая валидация по name
function softValidateByName(name, want) {
  const nm = normalizeStr(name);
  
  if (want.typeTok && !nm.includes(want.typeTok)) return false;
  if (want.stdToks.length && !want.stdToks.some(t => nm.includes(t))) return false;
  
  let ok = 0;
  if (want.mxlToks.length && want.mxlToks.some(t => nm.includes(normalizeStr(t)))) ok++;
  if (want.coatToks.length && want.coatToks.some(t => nm.includes(normalizeStr(t)))) ok++;
  if (want.materialToks.length && want.materialToks.some(t => nm.includes(normalizeStr(t)))) ok++;
  
  // требуем как минимум mxl или материал/покрытие
  return ok >= 1;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { search_query, user_intent } = await req.json();
    
    console.log('🔍 FastenerSearch: Получен запрос:', { 
      search_query, 
      user_intent_type: user_intent?.type,
      is_simple_parsed: user_intent?.is_simple_parsed 
    });

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? ""
    );

    // ---- подготавливаем токены из intent ----
    
    // Тип детали (универсальный)
    const typeTok = user_intent?.type ? normalizeStr(user_intent.type) : null;
    
    // Стандарты (универсальные)
    const stdToks = [];
    if (user_intent?.standard) {
      const standard = user_intent.standard.toLowerCase();
      stdToks.push(standard);
      
      // Добавляем варианты записи стандарта
      if (standard.includes("din")) {
        stdToks.push(standard.replace(/\s+/g, "")); // DIN965
        stdToks.push(standard.replace(/\s+/g, " ")); // DIN 965
      }
      if (standard.includes("iso")) {
        stdToks.push(standard.replace(/\s+/g, "")); // ISO7380
        stdToks.push(standard.replace(/\s+/g, " ")); // ISO 7380
      }
    }
    
    // Размеры (диаметр x длина)
    const mxlToks = mxlVariants(user_intent?.diameter, user_intent?.length);
    
    // Покрытия (универсальные)
    const coatToks = [];
    if (user_intent?.coating) {
      const coating = user_intent.coating.toLowerCase();
      coatToks.push(coating);
      
      // Добавляем варианты записи покрытия
      if (coating.includes("цинк")) {
        coatToks.push("цинк", "оцинк", "оцинкованный");
      }
      if (coating.includes("хром")) {
        coatToks.push("хром", "хромированный");
      }
      if (coating.includes("крашен")) {
        coatToks.push("крашен", "крашеный");
      }
    }
    
    // Материалы (универсальные)
    const materialToks = [];
    if (user_intent?.material) {
      const material = user_intent.material.toLowerCase();
      materialToks.push(material);
      
      // Добавляем варианты записи материала
      if (material.includes("нержавеющая")) {
        materialToks.push("нержавеющая", "нержавейка", "a2", "a4");
      }
      if (material.includes("сталь")) {
        materialToks.push("сталь", "8.8", "10.9", "12.9");
      }
    }
    
    // Класс прочности
    const gradeToks = [];
    if (user_intent?.grade) {
      const grade = user_intent.grade.toLowerCase();
      gradeToks.push(grade);
    }

    console.log('🔍 FastenerSearch: Подготовленные токены:', {
      typeTok, stdToks, mxlToks, coatToks, materialToks, gradeToks
    });

    // ---- ШАГ 1. Строгий AND по name ----
    let q = supabase.from("parts_catalog").select("*");
    
    // Исключаем негативные типы
    for (const neg of NEGATIVE_TYPES) {
      q = q.not("name", "ilike", `%${neg}%`).not("type", "ilike", `%${neg}%`);
    }
    
    // Тип детали
    if (typeTok) {
      q = q.ilike("name", `%${escapeSqlLike(typeTok)}%`);
    }
    
    // Стандарты (OR)
    if (stdToks.length) {
      const stdConds = stdToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      q = q.or(stdConds);
    }
    
    // Размеры (OR)
    if (mxlToks.length) {
      const mxlConds = mxlToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      q = q.or(mxlConds);
    }
    
    // Покрытия (OR)
    if (coatToks.length) {
      const coatConds = coatToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      q = q.or(coatConds);
    }
    
    // Материалы (OR)
    if (materialToks.length) {
      const materialConds = materialToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      q = q.or(materialConds);
    }
    
    // Классы прочности (OR)
    if (gradeToks.length) {
      const gradeConds = gradeToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      q = q.or(gradeConds);
    }

    const { data: strictData, error: strictErr } = await q.limit(200);
    if (strictErr) console.error("strict AND err:", strictErr);
    
    let results = (strictData || []).filter(r => softValidateByName(r.name || "", {
      typeTok,
      stdToks,
      mxlToks,
      coatToks,
      materialToks
    }));
    
    console.log("🔍 FastenerSearch: Строгий AND найден:", results.length);

    // ---- ШАГ 2. Расслабленный OR (если строгий поиск не дал результатов) ----
    if (!results.length) {
      const orConds = [];
      
      if (typeTok) orConds.push(`name.ilike.%${escapeSqlLike(typeTok)}%`);
      if (stdToks.length) {
        for (const t of stdToks) orConds.push(`name.ilike.%${escapeSqlLike(t)}%`);
      }
      for (const t of mxlToks) orConds.push(`name.ilike.%${escapeSqlLike(t)}%`);
      for (const t of coatToks) orConds.push(`name.ilike.%${escapeSqlLike(t)}%`);
      for (const t of materialToks) orConds.push(`name.ilike.%${escapeSqlLike(t)}%`);
      for (const t of gradeToks) orConds.push(`name.ilike.%${escapeSqlLike(t)}%`);
      
      let qb = supabase.from("parts_catalog").select("*");
      
      // Исключаем негативные типы
      for (const neg of NEGATIVE_TYPES) {
        qb = qb.not("name", "ilike", `%${neg}%`).not("type", "ilike", `%${neg}%`);
      }
      
      if (orConds.length) {
        qb = qb.or(orConds.join(","));
      }
      
      const { data: looseData, error: looseErr } = await qb.limit(200);
      if (looseErr) console.error("loose OR err:", looseErr);
      
      results = (looseData || []).filter(r => softValidateByName(r.name || "", {
        typeTok,
        stdToks,
        mxlToks,
        coatToks,
        materialToks
      }));
      
      console.log("🔍 FastenerSearch: Расслабленный OR найден:", results.length);
    }

    // ---- Ранжирование результатов ----
    const rank = (name) => {
      const n = normalizeStr(name);
      let s = 0;
      
      // Тип детали (высший приоритет)
      if (typeTok && n.includes(typeTok)) s += 10;
      
      // Стандарт (высокий приоритет)
      if (stdToks.some(t => n.includes(t))) s += 8;
      
      // Размеры (высокий приоритет)
      if (mxlToks.some(t => n.includes(normalizeStr(t)))) s += 7;
      
      // Класс прочности (средний приоритет)
      if (gradeToks.some(t => n.includes(t))) s += 6;
      
      // Материал (средний приоритет)
      if (materialToks.some(t => n.includes(normalizeStr(t)))) s += 5;
      
      // Покрытие (низкий приоритет)
      if (coatToks.some(t => n.includes(normalizeStr(t)))) s += 3;
      
      return s;
    };

    const ranked = results.map(it => ({
      ...it,
      relevance_score: rank(it.name || ""),
      probability_percent: Math.min(rank(it.name || "") * 10, 100), // Преобразуем в проценты
      match_reason: getMatchReason(it.name || "", {
        typeTok, stdToks, mxlToks, coatToks, materialToks, gradeToks
      })
    })).sort((a, b) => b.relevance_score - a.relevance_score);

    console.log("🔍 FastenerSearch: Отранжировано результатов:", ranked.length);
    if (ranked.length > 0) {
      console.log("🔍 FastenerSearch: Топ-3 по релевантности:", 
        ranked.slice(0, 3).map(r => ({ 
          name: r.name, 
          sku: r.sku, 
          score: r.relevance_score,
          reason: r.match_reason 
        }))
      );
    }

    return new Response(JSON.stringify({
      results: ranked,
      search_metadata: {
        query_type: user_intent?.is_simple_parsed ? 'simple' : 'complex',
        total_results: ranked.length,
        search_time_ms: Date.now(),
        used_fallback: results.length === 0
      }
    }), {
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json"
      },
      status: 200
    });

  } catch (e) {
    console.error("❌ FastenerSearch: Критическая ошибка:", e);
    return new Response(JSON.stringify({
      error: "Internal error",
      details: e?.message || String(e)
    }), {
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json"
      },
      status: 500
    });
  }
});

// Функция для определения причины совпадения
function getMatchReason(name, tokens) {
  const n = normalizeStr(name);
  
  if (tokens.typeTok && n.includes(tokens.typeTok) && 
      tokens.mxlToks.some(t => n.includes(normalizeStr(t)))) {
    return 'Точное совпадение типа и размеров';
  }
  
  if (tokens.typeTok && n.includes(tokens.typeTok)) {
    return 'Совпадение типа детали';
  }
  
  if (tokens.stdToks.some(t => n.includes(t))) {
    return 'Совпадение стандарта';
  }
  
  if (tokens.mxlToks.some(t => n.includes(normalizeStr(t)))) {
    return 'Совпадение размеров';
  }
  
  if (tokens.gradeToks.some(t => n.includes(t))) {
    return 'Совпадение класса прочности';
  }
  
  if (tokens.materialToks.some(t => n.includes(normalizeStr(t)))) {
    return 'Совпадение материала';
  }
  
  if (tokens.coatToks.some(t => n.includes(normalizeStr(t)))) {
    return 'Совпадение покрытия';
  }
  
  return 'Частичное совпадение по названию';
}
