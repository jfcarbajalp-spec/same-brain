# -*- coding: utf-8 -*-
"""Amor, pareja, relaciones y citas.

Reglas: siempre sobre las opiniones y preferencias del propio jugador.
Nunca sobre otros jugadores de la partida.
"""

TEMA = "amor"

PREGUNTAS = [
    ("¿Crees en el amor a primera vista?",
     ["💘 Sí, completamente", "🤔 Puede pasar", "😐 No mucho", "🚫 Para nada"]),

    ("¿Qué pesa más al enamorarte?",
     ["✨ Atracción", "🧠 Personalidad", "🧭 Valores", "😂 Sentido del humor"]),

    ("¿Qué elegirías para una primera cita?",
     ["🏖️ Playa", "🍸 Bar", "🍽️ Cena", "🎳 Una actividad juntos"]),

    ("¿Qué sería más difícil de perdonar en una relación?",
     ["🤥 Una mentira importante", "💔 Una infidelidad", "🫥 Falta de apoyo", "🕳️ Que oculten algo mucho tiempo"]),

    ("¿Qué valoras más en una pareja?",
     ["🤝 Lealtad", "🕊️ Independencia", "🫂 Cariño", "😂 Sentido del humor"]),

    ("¿Qué hace que una relación funcione?",
     ["🗣️ Comunicación", "🔥 Atracción", "🧭 Valores compartidos", "🌬️ Dar espacio"]),

    ("¿Podrías tener una relación a distancia?",
     ["✅ Sí", "⏳ Solo temporalmente", "🤷 Depende muchísimo de la persona", "🚫 Nunca"]),

    ("¿Qué te parece más romántico?",
     ["✈️ Un viaje juntos", "🍽️ Una cena", "💌 Una carta", "🎁 Una sorpresa espontánea"]),

    ("¿Cuánto tardarías en decir 'te quiero'?",
     ["⚡ Si lo siento, lo digo ya", "📅 Unos meses", "🐢 Muchísimo", "🤐 Prefiero demostrarlo"]),

    ("¿Qué es peor en una cita?",
     ["📱 Que mire el móvil", "🗣️ Que solo hable de sí mismo", "😶 Silencios eternos", "💸 Que discuta por la cuenta"]),

    ("¿Quién paga en la primera cita?",
     ["➗ A medias", "🙋 El que invita", "🔁 Uno esta vez, otro la siguiente", "🤷 Me da igual"]),

    ("¿Qué te atrae más al principio?",
     ["👀 La mirada", "🗣️ Cómo habla", "😂 Cómo te hace reír", "🎯 La seguridad"]),

    ("¿Presentarías a tu pareja a tus amigos pronto?",
     ["⚡ Enseguida", "📅 Después de unos meses", "🐢 Lo más tarde posible", "🤷 Depende del grupo"]),

    ("¿Qué opinas de discutir en pareja?",
     ["🗣️ Sano si se habla bien", "😬 Lo evito siempre", "🔥 Prefiero soltarlo todo", "🚪 Necesito irme y volver"]),

    ("¿Qué te haría dudar de una relación?",
     ["🧊 Que se enfríe", "🗺️ Querer cosas distintas", "😶 Que no se hable de nada", "👥 Que no encaje con mi gente"]),

    ("¿Cuál es tu idea de un plan perfecto en pareja?",
     ["🛋️ Sofá y no salir", "🥾 Una excursión", "🍷 Cena y hablar horas", "🎉 Salir con más gente"]),

    ("¿Qué es más importante en el día a día?",
     ["☕ Los detalles pequeños", "🗓️ Los planes grandes", "🫂 Estar disponible", "🕊️ No agobiar"]),

    ("¿Qué opinas de las apps de citas?",
     ["📱 Funcionan perfectamente", "🤷 Están bien para conocer gente", "😬 No es lo mío", "🚫 Prefiero en persona"]),

    ("¿Segundas oportunidades?",
     ["💚 Siempre", "🤔 Una y solo una", "🚫 Nunca", "🔍 Depende de lo que pasó"]),

    ("¿Qué te define en una relación?",
     ["🫂 Muy detallista", "🕊️ Muy independiente", "🗣️ Muy hablador", "😌 Muy tranquilo"]),

    ("¿Qué harías si te gusta alguien?",
     ["🎯 Se lo digo directamente", "🎣 Lanzo señales", "⏳ Espero a que dé el paso", "🤐 No hago nada"]),

    ("¿Se puede ser amigo de un ex?",
     ["✅ Perfectamente", "⏳ Con tiempo, sí", "😬 Difícil", "🚫 Imposible"]),

    ("¿Qué te da más seguridad en una relación?",
     ["🗣️ Que hablemos de todo", "📅 Planes de futuro", "🫂 Cómo me trata delante de otros", "🕊️ Confianza sin preguntar"]),

    ("¿Celos?",
     ["😌 Casi nunca", "🙂 Un poco es normal", "😬 Más de lo que me gustaría", "🚫 Ninguno, y lo espero igual"]),

    ("¿Qué gesto te conquista más?",
     ["🍳 Que te cocine algo", "🎧 Que se acuerde de un detalle mínimo", "🚗 Que aparezca cuando estás mal", "😂 Que te haga llorar de risa"]),

    ("¿Vivir juntos pronto o tarde?",
     ["🏠 Cuanto antes", "📅 Después de un par de años", "🐢 Lo más tarde posible", "🚪 Prefiero casas separadas"]),

    ("¿Qué haces cuando una relación se acaba?",
     ["🧹 Corte limpio y a otra cosa", "😢 Necesito duelo largo", "👥 Salgo con todo el mundo", "💼 Me vuelco en el trabajo"]),

    ("¿Qué es lo mínimo innegociable?",
     ["💯 Honestidad", "🫂 Respeto a mi gente", "🕊️ Mi espacio", "🎯 Que quiera lo mismo que yo"]),

    ("¿Qué opinas de las relaciones que empiezan como amistad?",
     ["💚 Son las mejores", "🤔 Arriesgado pero vale la pena", "😬 Mejor no mezclar", "🤷 Depende del caso"]),

    ("¿Qué prefieres en el día a día con tu pareja?",
     ["🔥 Que nos sorprendamos siempre", "🛋️ Rutina cómoda", "⚖️ Rutina con chispa", "🌍 Cada uno con su vida y juntos"]),
]
