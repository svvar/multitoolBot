import gettext

from babel import Locale

countries = {
    'uk':{
        'uk_UA': '🇺🇦 Україна', 'en_GB': '🇬🇧 Великобританія', 'en_PH': '🇵🇭 Філіппіни', 'es_MX': '🇲🇽 Мексика', 'es_CL': '🇨🇱 Чилі',
        'ru_RU': '🇷🇺 Росія', 'pt_BR': '🇧🇷 Бразилія', 'en_AU': '🇦🇺 Австралія', 'de_DE': '🇩🇪 Німеччина', 'en_US': '🇺🇸 США',
        'pl_PL': '🇵🇱 Польща', 'az_AZ': '🇦🇿 Азербайджан', 'bg_BG': '🇧🇬 Болгарія', 'cs_CZ': '🇨🇿 Чехія', 'da_DK': '🇩🇰 Данія',
        'de_AT': '🇦🇹 Австрія', 'de_CH': '🇨🇭 Швейцарія',  'el_GR': '🇬🇷 Греція', 'es_ES': '🇪🇸 Іспанія',
        'et_EE': '🇪🇪 Естонія', 'fi_FI': '🇫🇮 Фінляндія', 'fr_FR': '🇫🇷 Франція', 'he_IL': '🇮🇱 Ізраїль',
        'hi_IN': '🇮🇳 Індія', 'hr_HR': '🇭🇷 Хорватія', 'hu_HU': '🇭🇺 Угорщина', 'hy_AM': '🇦🇲 Вірменія', 'id_ID': '🇮🇩 Індонезія',
        'it_IT': '🇮🇹 Італія', 'ja_JP': '🇯🇵 Японія', 'ko_KR': '🇰🇷 Південна Корея', 'lt_LT': '🇱🇹 Литва', 'lv_LV': '🇱🇻 Латвія',
        'nl_NL': '🇳🇱 Нідерланди',   'pt_PT': '🇵🇹 Португалія', 'ro_RO': '🇷🇴 Румунія',
        'sk_SK': '🇸🇰 Словаччина', 'sl_SI': '🇸🇮 Словенія', 'sv_SE': '🇸🇪 Швеція', 'tr_TR': '🇹🇷 Туреччина',

    },
    'ru':{
        'uk_UA': '🇺🇦 Украина', 'en_GB': '🇬🇧 Великобритания', 'en_PH': '🇵🇭 Филиппины', 'es_MX': '🇲🇽 Мексика', 'es_CL': '🇨🇱 Чили',
        'ru_RU': '🇷🇺 Россия', 'pt_BR': '🇧🇷 Бразилия', 'en_AU': '🇦🇺 Австралия', 'de_DE': '🇩🇪 Германия', 'en_US': '🇺🇸 США',
        'pl_PL': '🇵🇱 Польша', 'az_AZ': '🇦🇿 Азербайджан', 'bg_BG': '🇧🇬 Болгария', 'cs_CZ': '🇨🇿 Чехия', 'da_DK': '🇩🇰 Дания',
        'de_AT': '🇦🇹 Австрия', 'de_CH': '🇨🇭 Швейцария', 'el_GR': '🇬🇷 Греция', 'es_ES': '🇪🇸 Испания',
        'et_EE': '🇪🇪 Эстония', 'fi_FI': '🇫🇮 Финляндия', 'fr_FR': '🇫🇷 Франция', 'he_IL': '🇮🇱 Израиль',
        'hi_IN': '🇮🇳 Индия', 'hr_HR': '🇭🇷 Хорватия', 'hu_HU': '🇭🇺 Венгрия', 'hy_AM': '🇦🇲 Армения', 'id_ID': '🇮🇩 Индонезия',
        'it_IT': '🇮🇹 Италия', 'ja_JP': '🇯🇵 Япония', 'ko_KR': '🇰🇷 Южная Корея', 'lt_LT': '🇱🇹 Литва', 'lv_LV': '🇱🇻 Латвия',
        'nl_NL': '🇳🇱 Нидерланды', 'pt_PT': '🇵🇹 Португалия', 'ro_RO': '🇷🇴 Румыния',
        'sk_SK': '🇸🇰 Словакия', 'sl_SI': '🇸🇮 Словения', 'sv_SE': '🇸🇪 Швеция', 'tr_TR': '🇹🇷 Турция',


    },
    'en':{
        'uk_UA': '🇺🇦 Ukraine', 'en_GB': '🇬🇧 United Kingdom', 'en_PH': '🇵🇭 Philippines', 'es_MX': '🇲🇽 Mexico', 'es_CL': '🇨🇱 Chile',
        'ru_RU': '🇷🇺 Russia', 'pt_BR': '🇧🇷 Brazil', 'en_AU': '🇦🇺 Australia', 'de_DE': '🇩🇪 Germany', 'en_US': '🇺🇸 United States',
        'pl_PL': '🇵🇱 Poland', 'az_AZ': '🇦🇿 Azerbaijan', 'bg_BG': '🇧🇬 Bulgaria', 'cs_CZ': '🇨🇿 Czech Republic', 'da_DK': '🇩🇰 Denmark',
        'de_AT': '🇦🇹 Austria', 'de_CH': '🇨🇭 Switzerland',  'el_GR': '🇬🇷 Greece', 'es_ES': '🇪🇸 Spain',
        'et_EE': '🇪🇪 Estonia', 'fi_FI': '🇫🇮 Finland', 'fr_FR': '🇫🇷 France', 'he_IL': '🇮🇱 Israel',
        'hi_IN': '🇮🇳 India', 'hr_HR': '🇭🇷 Croatia', 'hu_HU': '🇭🇺 Hungary', 'hy_AM': '🇦🇲 Armenia', 'id_ID': '🇮🇩 Indonesia',
        'it_IT': '🇮🇹 Italy', 'ja_JP': '🇯🇵 Japan', 'ko_KR': '🇰🇷 South Korea', 'lt_LT': '🇱🇹 Lithuania', 'lv_LV': '🇱🇻 Latvia',
        'nl_NL': '🇳🇱 Netherlands', 'pt_PT': '🇵🇹 Portugal', 'ro_RO': '🇷🇴 Romania',
        'sk_SK': '🇸🇰 Slovakia', 'sl_SI': '🇸🇮 Slovenia', 'sv_SE': '🇸🇪 Sweden', 'tr_TR': '🇹🇷 Turkey',



    }
}
locales = {
    'az_AZ': 'Azerbaijan',
    'bg_BG': 'Bulgaria',
    'cs_CZ': 'Czech Republic',
    'da_DK': 'Denmark',
    'de_AT': 'Austria',
    'de_CH': 'Switzerland',
    'de_DE': 'Germany',
    'el_GR': 'Greece',
    'en_AU': 'Australia',
    'en_GB': 'United Kingdom',
    'en_US': 'United States',
    'en_PH': 'Philippines',
    'es_ES': 'Spain',
    'es_MX': 'Mexico',
    'es_CL': 'Chile',
    'et_EE': 'Estonia',
    'fi_FI': 'Finland',
    'fr_FR': 'France',
    'he_IL': 'Israel',
    'hi_IN': 'India',
    'hr_HR': 'Croatia',
    'hu_HU': 'Hungary',
    'hy_AM': 'Armenia',
    'id_ID': 'Indonesia',
    'it_IT': 'Italy',
    'ja_JP': 'Japan',
    'ko_KR': 'South Korea',
    'lt_LT': 'Lithuania',
    'lv_LV': 'Latvia',
    'nl_NL': 'Netherlands',
    'pl_PL': 'Poland',
    'pt_BR': 'Brazil',
    'pt_PT': 'Portugal',
    'ro_RO': 'Romania',
    'ru_RU': 'Russia',
    'sk_SK': 'Slovakia',
    'sl_SI': 'Slovenia',
    'sv_SE': 'Sweden',
    'tr_TR': 'Turkey',
    'uk_UA': 'Ukraine',
}

def translate_string(locale_name, message_original):
    user_locale = Locale.parse(locale_name)

    translations = gettext.translation(
        domain='messages',
        localedir='locales',
        languages=[str(user_locale)]
    )

    _ = translations.gettext

    translated_message = _(message_original)
    return translated_message
