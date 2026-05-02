BUILDING_CONFIG = {
    '🏠 Жилой дом': {
        'cost': 150, 
        'income': 15, 
        'residents': 50, 
        'jobs': 0, 
        'min_level': 1,
        'icon': '🏠'
    },
    '🛒 Магазин': {
        'cost': 350, 
        'income': 70, 
        'residents': 0, 
        'jobs': 15, 
        'min_level': 1,
        'icon': '🛒'
    },
    '🏭 Завод': {
        'cost': 1500, 
        'income': 200, 
        'residents': 0, 
        'jobs': 40, 
        'min_level': 5,
        'icon': '🏭'
    },
    '🌳 Парк': {
        'cost': 2000, 
        'income': 0, 
        'residents': 0, 
        'jobs': 5, 
        'min_level': 7,
        'icon': '🌳'
    },
    '🚨 Полиция': {
        'cost': 5000, 
        'income': -50, 
        'residents': 0, 
        'jobs': 20, 
        'min_level': 10, 
        'icon': '🚨',
        'desc': 'Защищает от плохих событий'
    },
    '🏥 Больница': {
        'cost': 4500, 
        'income': -100, 
        'residents': 0, 
        'jobs': 30, 
        'min_level': 10, 
        'icon': '🏥',
        'desc': 'Увеличивает прирост населения'
    },
    '👨‍🚒 Пожарные': {
        'cost': 3500, 
        'income': -40, 
        'residents': 0, 
        'jobs': 15, 
        'min_level': 10, 
        'icon': '👨‍🚒',
        'desc': 'Снижает шанс катастроф'
    },
    '🏛 Ратуша': {
        'cost': 10000, 
        'income': 200, 
        'residents': 0, 
        'jobs': 50,
        'min_level': 20,
        'icon': '🏛',
        'desc': 'Позволяет собирать больше налогов'
    }
}

GAME_SETTINGS = {
    'tax_cooldown': 3600,
    'base_happiness': 50,
    'xp_per_build': 50,
    'xp_per_collect': 10
}