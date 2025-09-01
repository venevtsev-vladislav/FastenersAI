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
  
  // Специальная обработка для уголков (формат 50x50x40)
  if (D.includes('x') && !D.startsWith('M')) {
    // Это уголок, возвращаем как есть
    const xs = ["x", "х", "×"];
    const out = [];
    for (const X of xs) {
      out.push(D.replace(/x/g, X), D.replace(/х/g, X), D.replace(/×/g, X));
    }
    return Array.from(new Set(out));
  }
  
  // Обычная обработка для болтов/винтов
  const dLat = D, dCyr = D.replace(/^M/, "М");
  const xs = ["x", "х", "×", "-"];
  const out = [];
  
  for (const X of xs) {
    out.push(`${dLat}${X}${L}`, `${dLat} ${X} ${L}`, `${dCyr}${X}${L}`, `${dCyr} ${X} ${L}`);
  }
  out.push(`${dLat}${L}`, `${dCyr}${L}`);

  // Дополнительно: если диаметр десятичный, генерируем варианты по дробной части (напр. 4.2 -> 2x90)
  const decimalMatch = D.match(/^(\d+)[\.,](\d+)$/);
  if (decimalMatch) {
    const fractional = decimalMatch[2];
    const altTokens = [
      `${fractional}x${L}`,
      `${fractional} x ${L}`,
      `${fractional}х${L}`,
      `${fractional} х ${L}`,
      `${fractional}×${L}`,
      `${fractional} × ${L}`
    ];
    out.push(...altTokens);
  }
  
  return Array.from(new Set(out));
}

// ---------- РАНЖИРОВАНИЕ ----------

// Интерфейсы для типизации
interface MatchAnalysis {
  type_match: boolean;
  standard_match: boolean;
  size_match: boolean;
  coating_match: boolean;
  matched_tokens: string[];
  explanation: string[];
}

interface ProbabilityData {
  probability: number;
  explanation: string;
}

interface RankingTokens {
  typeTok: string | null;
  stdToks: string[];
  mxlToks: string[];
  coatToks: string[];
}

// Функция для определения причины совпадения
function getMatchReason(name: string, tokens: RankingTokens): string {
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
  
  if (tokens.coatToks.some(t => n.includes(normalizeStr(t)))) {
    return 'Совпадение покрытия';
  }
  
  return 'Частичное совпадение по названию';
}

// Функция для детального анализа совпадений
function analyzeMatches(name: string, tokens: RankingTokens): MatchAnalysis {
  const n = normalizeStr(name);
  const analysis: MatchAnalysis = {
    type_match: false,
    standard_match: false,
    size_match: false,
    coating_match: false,
    matched_tokens: [],
    explanation: []
  };
  
  console.log(`🔍 analyzeMatches: Анализируем "${name}"`);
  console.log(`🔍 analyzeMatches: Нормализованное название: "${n}"`);
  console.log(`🔍 analyzeMatches: Токены для поиска:`, tokens);
  
  // Проверяем совпадение типа
  if (tokens.typeTok && n.includes(tokens.typeTok)) {
    analysis.type_match = true;
    analysis.matched_tokens.push(tokens.typeTok);
    analysis.explanation.push(`✅ Совпадение типа: "${tokens.typeTok}"`);
    console.log(`🔍 analyzeMatches: ✅ Найдено совпадение типа: "${tokens.typeTok}"`);
  } else if (tokens.typeTok) {
    console.log(`🔍 analyzeMatches: ❌ Не найдено совпадение типа: "${tokens.typeTok}"`);
  }
  
  // Проверяем совпадение стандарта
  const matchedStandards = tokens.stdToks.filter(t => n.includes(t));
  if (matchedStandards.length > 0) {
    analysis.standard_match = true;
    analysis.matched_tokens.push(...matchedStandards);
    analysis.explanation.push(`✅ Совпадение стандарта: "${matchedStandards.join(', ')}"`);
    console.log(`🔍 analyzeMatches: ✅ Найдено совпадение стандарта: "${matchedStandards.join(', ')}"`);
  } else if (tokens.stdToks.length > 0) {
    console.log(`🔍 analyzeMatches: ❌ Не найдено совпадение стандарта: "${tokens.stdToks.join(', ')}"`);
  }
  
  // Проверяем совпадение размеров
  const matchedSizes = tokens.mxlToks.filter(t => n.includes(normalizeStr(t)));
  if (matchedSizes.length > 0) {
    analysis.size_match = true;
    analysis.matched_tokens.push(...matchedSizes);
    analysis.explanation.push(`✅ Совпадение размеров: "${matchedSizes.join(', ')}"`);
    console.log(`🔍 analyzeMatches: ✅ Найдено совпадение размеров: "${matchedSizes.join(', ')}"`);
  } else if (tokens.mxlToks.length > 0) {
    console.log(`🔍 analyzeMatches: ❌ Не найдено совпадение размеров: "${tokens.mxlToks.join(', ')}"`);
    console.log(`🔍 analyzeMatches: Искали токены:`, tokens.mxlToks.map(t => normalizeStr(t)));
  }
  
  // Проверяем совпадение покрытия
  const matchedCoatings = tokens.coatToks.filter(t => n.includes(normalizeStr(t)));
  if (matchedCoatings.length > 0) {
    analysis.coating_match = true;
    analysis.matched_tokens.push(...matchedCoatings);
    analysis.explanation.push(`✅ Совпадение покрытия: "${matchedCoatings.join(', ')}"`);
    console.log(`🔍 analyzeMatches: ✅ Найдено совпадение покрытия: "${matchedCoatings.join(', ')}"`);
  } else if (tokens.coatToks.length > 0) {
    console.log(`🔍 analyzeMatches: ❌ Не найдено совпадение покрытия: "${tokens.coatToks.join(', ')}"`);
  }
  
  console.log(`🔍 analyzeMatches: Итоговый анализ:`, analysis);
  return analysis;
}

// Функция для вычисления probability_percent с весами
function calculateProbability(analysis: MatchAnalysis): ProbabilityData {
  let totalScore = 0;
  const weights = {
    type: 25,        // 25% за тип детали
    standard: 40,    // 40% за стандарт DIN
    size: 30,        // 30% за точные размеры
    coating: 15      // 15% за покрытие
  };
  
  const explanation = [...analysis.explanation];
  
  // Базовые очки за каждый тип совпадения
  if (analysis.type_match) {
    totalScore += weights.type;
    explanation.push(`📊 Вклад типа: +${weights.type}%`);
  }
  
  if (analysis.standard_match) {
    totalScore += weights.standard;
    explanation.push(`📊 Вклад стандарта: +${weights.standard}%`);
  }
  
  if (analysis.size_match) {
    totalScore += weights.size;
    explanation.push(`📊 Вклад размеров: +${weights.size}%`);
  }
  
  if (analysis.coating_match) {
    totalScore += weights.coating;
    explanation.push(`📊 Вклад покрытия: +${weights.coating}%`);
  }
  
  // Бонусы за комбинации
  if (analysis.standard_match && analysis.size_match) {
    const bonus = 15;
    totalScore += bonus;
    explanation.push(`🎯 Бонус за стандарт + размеры: +${bonus}%`);
  }
  
  if (analysis.type_match && analysis.size_match) {
    const bonus = 10;
    totalScore += bonus;
    explanation.push(`🎯 Бонус за тип + размеры: +${bonus}%`);
  }
  
  if (analysis.type_match && analysis.standard_match && analysis.size_match) {
    const bonus = 20;
    totalScore += bonus;
    explanation.push(`🎯 Бонус за полное совпадение: +${bonus}%`);
  }
  
  // Ограничения согласно требованиям
  if (analysis.standard_match && analysis.size_match) {
    // Если совпали и стандарт, и размеры, вероятность должна быть не меньше 80-90%
    totalScore = Math.max(totalScore, 80);
    if (totalScore > 80) {
      explanation.push(`🔒 Минимальная вероятность для стандарт+размеры: 80%`);
    }
  } else if (analysis.type_match && !analysis.size_match && !analysis.standard_match) {
    // Если совпал только тип без размеров и стандарта — не более 40%
    totalScore = Math.min(totalScore, 40);
    explanation.push(`🔒 Максимальная вероятность для только типа: 40%`);
  } else if (analysis.coating_match && !analysis.type_match && !analysis.size_match && !analysis.standard_match) {
    // Если совпало только покрытие — не более 20%
    totalScore = Math.min(totalScore, 20);
    explanation.push(`🔒 Максимальная вероятность для только покрытия: 20%`);
  }
  
  // Нормализация в диапазон 0-100%
  const probability = Math.max(0, Math.min(100, Math.round(totalScore)));
  
  explanation.push(`📈 Итоговая вероятность: ${probability}%`);
  
  // Логирование для отладки
  console.log("🔍 calculateProbability: Детали расчета:", {
    totalScore,
    probability,
    type_match: analysis.type_match,
    standard_match: analysis.standard_match,
    size_match: analysis.size_match,
    coating_match: analysis.coating_match
  });
  
  return {
    probability,
    explanation: explanation.join('\n')
  };
}

// Основная функция ранжирования
function rankResults(results: any[], tokens: RankingTokens, search_query: string) {
  return results.map(it => {
    const analysis = analyzeMatches(it.name || "", tokens);
    const probabilityData = calculateProbability(analysis);
    
    return {
      ...it,
      relevance_score: probabilityData.probability,
      probability_percent: probabilityData.probability,
      match_reason: getMatchReason(it.name || "", tokens),
      explanation: probabilityData.explanation,
      matched_tokens: analysis.matched_tokens,
      search_query: search_query,
      full_query: search_query
    };
  }).sort((a, b) => b.probability_percent - a.probability_percent);
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

    // ---- ПОИСК ПО ПРИОРИТЕТУ ----
    
    // Тип детали
    const typeTok = user_intent?.type ? normalizeStr(user_intent.type) : null;
    
    // Стандарты
    const stdToks = [];
    if (user_intent?.standard) {
      const standard = user_intent.standard.toLowerCase();
      stdToks.push(standard);
      if (standard.includes("din")) {
        stdToks.push(standard.replace(/\s+/g, "")); // DIN965
        stdToks.push(standard.replace(/\s+/g, " ")); // DIN 965
      }
    }
    
    // Размеры
    const mxlToks = mxlVariants(user_intent?.diameter, user_intent?.length);
    
    // Покрытия
    const coatToks = [];
    if (user_intent?.coating) {
      const coating = user_intent.coating.toLowerCase();
      coatToks.push(coating);
      if (coating.includes("цинк")) {
        coatToks.push("цинк", "оцинк", "оцинкованный");
      }
    }

    console.log('🔍 FastenerSearch: Подготовленные токены:', {
      typeTok, stdToks, mxlToks, coatToks
    });
    
    // Детальное логирование токенов размеров
    if (mxlToks.length > 0) {
      console.log('🔍 FastenerSearch: Токены размеров:', mxlToks);
      console.log('🔍 FastenerSearch: Исходные размеры:', {
        diameter: user_intent?.diameter,
        length: user_intent?.length
      });
    }

    let results = [];

    // ---- ШАГ 1: Векторный поиск по типу + размеры ----
    if (typeTok && mxlToks.length > 0) {
      console.log("🔍 Шаг 1: Векторный поиск по типу + размеры");
      
      // Создаем поисковый запрос для векторного поиска (websearch, русская морфология)
      const searchQuery = [typeTok, ...mxlToks].join(" ");
      console.log("🔍 Векторный запрос:", searchQuery);
      
      const { data: step1Results, error } = await supabase
        .from("parts_catalog")
        .select("*")
        .textSearch("search_vector", searchQuery, { config: "russian", type: "websearch" })
        .limit(20);
      
      if (error) console.error("Шаг 1 ошибка:", error);
      
      results = step1Results || [];
      console.log("🔍 Шаг 1 найдено:", results.length);
    }

    // ---- ШАГ 2: Векторный поиск только по типу ----
    if (results.length === 0 && typeTok) {
      console.log("🔍 Шаг 2: Векторный поиск только по типу");
      
      const searchQuery = typeTok;
      console.log("🔍 Векторный запрос:", searchQuery);
      
      const { data: step2Results, error } = await supabase
        .from("parts_catalog")
        .select("*")
        .textSearch("search_vector", searchQuery, { config: "russian", type: "websearch" })
        .limit(20);
      
      if (error) console.error("Шаг 2 ошибка:", error);
      
      results = step2Results || [];
      console.log("🔍 Шаг 2 найдено:", results.length);
    }

    // ---- ШАГ 3: Векторный поиск по размеру ----
    if (results.length === 0 && mxlToks.length > 0) {
      console.log("🔍 Шаг 3: Векторный поиск по размеру");
      
      const searchQuery = mxlToks.join(" ");
      console.log("🔍 Векторный запрос:", searchQuery);
      
      const { data: step3Results, error } = await supabase
        .from("parts_catalog")
        .select("*")
        .textSearch("search_vector", searchQuery, { config: "russian", type: "websearch" })
        .limit(20);
      
      if (error) console.error("Шаг 3 ошибка:", error);
      
      results = step3Results || [];
      console.log("🔍 Шаг 3 найдено:", results.length);
    }

    // ---- ШАГ 4: Поиск по стандарту ----
    if (results.length === 0 && stdToks.length > 0) {
      console.log("🔍 Шаг 4: Поиск по стандарту");
      
      const stdConds = stdToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      
      const { data: step4Results, error } = await supabase
        .from("parts_catalog")
        .select("*")
        .or(stdConds)
        .limit(20);
      
      if (error) console.error("Шаг 4 ошибка:", error);
      
      results = step4Results || [];
      console.log("🔍 Шаг 4 найдено:", results.length);
    }

    // ---- ШАГ 5: Поиск по покрытию ----
    if (results.length === 0 && coatToks.length > 0) {
      console.log("🔍 Шаг 5: Поиск по покрытию");
      
      const coatConds = coatToks.map(t => `name.ilike.%${escapeSqlLike(t)}%`).join(",");
      
      const { data: step5Results, error } = await supabase
        .from("parts_catalog")
        .select("*")
        .or(coatConds)
        .limit(20);
      
      if (error) console.error("Шаг 5 ошибка:", error);
      
      results = step5Results || [];
      console.log("🔍 Шаг 5 найдено:", results.length);
    }

    console.log("🔍 FastenerSearch: Итого найдено результатов:", results.length);

    // ---- Ранжирование результатов ----
    const tokens: RankingTokens = { typeTok, stdToks, mxlToks, coatToks };
    const ranked = rankResults(results, tokens, search_query);

    console.log("🔍 FastenerSearch: Отранжировано результатов:", ranked.length);
    if (ranked.length > 0) {
      console.log("🔍 FastenerSearch: Топ-3 по релевантности:", 
        ranked.slice(0, 3).map(r => ({ 
          name: r.name, 
          sku: r.sku, 
          score: r.relevance_score,
          probability_percent: r.probability_percent,
          reason: r.match_reason 
        }))
      );
      
      // Детальное логирование первого результата для отладки
      const firstResult = ranked[0];
      console.log("🔍 FastenerSearch: Детали первого результата:", {
        name: firstResult.name,
        sku: firstResult.sku,
        probability_percent: firstResult.probability_percent,
        relevance_score: firstResult.relevance_score,
        match_reason: firstResult.match_reason,
        explanation: firstResult.explanation,
        matched_tokens: firstResult.matched_tokens
      });
    }

    return new Response(JSON.stringify({
      results: ranked,
      search_metadata: {
        query_type: user_intent?.is_simple_parsed ? 'simple' : 'complex',
        total_results: ranked.length,
        search_time_ms: Date.now(),
        used_fallback: false
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