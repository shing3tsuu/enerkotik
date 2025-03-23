from dataclasses import dataclass
from fake_useragent import UserAgent
from parsing import *

ua = UserAgent().random

def create_shop_config(main_class, main_link, name_class, name_link, cost_class, cost_link):
    return ScraperConfig(
        main_class=main_class,
        main_link=main_link,
        name_class=name_class,
        name_link=name_link,
        cost_class=cost_class,
        cost_link=cost_link
    )

# Магнит
cookies_magnit = {
    '_ym_uid': '1731567664913563808',
    '_ym_d': '1731567664',
    'tmr_lvid': 'ccc542bdcc1744c0cad153d6034358de',
    'tmr_lvidTS': '1731567707863',
    'oxxfgh': '26173a82-f50f-415a-b528-37bf455623c1#0#7884000000#5000#1800000#12840',
    'KFP_DID': 'd23855c0-c3a1-8d7b-62d1-81727a0b1b40',
    'mindboxDeviceUUID': '7e89d50c-f933-4f00-8f5d-00467579af08',
    'directCrm-session': '%7B%22deviceGuid%22%3A%227e89d50c-f933-4f00-8f5d-00467579af08%22%7D',
    '_ga_8Z0Z2T2XNT': 'GS1.2.1731567708.1.0.1731567708.0.0.0',
    '_ga_72BLMGVWY6': 'GS1.1.1731567707.1.0.1731567747.0.0.0',
    '_ga': 'GA1.1.503503548.1731567664',
    '_ym_isad': '2',
    '_ym_visorc': 'b',
    'nmg_udi': '2490263E-082A-41AC-4226-8D14482369B5',
    'x_device_id': '2490263E-082A-41AC-4226-8D14482369B5',
    '_ga_L0N0B74HJP': 'GS1.1.1732135910.2.1.1732135948.22.0.0',
    'shopCode': '852714',
    'x_shop_type': 'MM',
    'nmg_sp': 'Y',
    'nmg_sid': '167309',
    'shopId': '167309',
}
headers_magnit = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    # 'Cookie': '_ym_uid=1731567664913563808; _ym_d=1731567664; tmr_lvid=ccc542bdcc1744c0cad153d6034358de; tmr_lvidTS=1731567707863; oxxfgh=26173a82-f50f-415a-b528-37bf455623c1#0#7884000000#5000#1800000#12840; KFP_DID=d23855c0-c3a1-8d7b-62d1-81727a0b1b40; mindboxDeviceUUID=7e89d50c-f933-4f00-8f5d-00467579af08; directCrm-session=%7B%22deviceGuid%22%3A%227e89d50c-f933-4f00-8f5d-00467579af08%22%7D; _ga_8Z0Z2T2XNT=GS1.2.1731567708.1.0.1731567708.0.0.0; _ga_72BLMGVWY6=GS1.1.1731567707.1.0.1731567747.0.0.0; _ga=GA1.1.503503548.1731567664; _ym_isad=2; _ym_visorc=b; nmg_udi=2490263E-082A-41AC-4226-8D14482369B5; x_device_id=2490263E-082A-41AC-4226-8D14482369B5; _ga_L0N0B74HJP=GS1.1.1732135910.2.1.1732135948.22.0.0; shopCode=852714; x_shop_type=MM; nmg_sp=Y; nmg_sid=167309; shopId=167309',
    'Referer': 'https://yandex.ru/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': ua,
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
params_magnit = {
    'shopCode': '852714',
    'shopType': '1',
}

magnit_connection = ConnectionParams(
    headers=headers_magnit,
    cookies=cookies_magnit,
    params=params_magnit
)

magnit_config = create_shop_config(
    main_class='article',
    main_link='unit-catalog-product-preview show-ratings',
    name_class='div',
    name_link='pl-text unit-catalog-product-preview-title',
    cost_class='span',
    cost_link='pl-text unit-catalog-product-preview-prices__regular'
)

magnit = ShopScraper(
    name='Магнит',
    link='https://magnit.ru/catalog/4883-energeticheskie_napitki?shopCode=852714&shopType=1&page=1',
    connection_params=magnit_connection,
    scraper_config=magnit_config,
    website_method='static'
)

cookies_pytorochka = {...}  # Ваши куки
headers_pytorochka = {...}  # Ваши заголовки

pytorochka_connection = ConnectionParams(
    headers=headers_pytorochka,
    cookies=cookies_pytorochka,
    params=None
)

pytorochka_config = create_shop_config(
    main_class='a',
    main_link='chakra-link xlSVIYdp- css-13jvj27',
    name_class='p',
    name_link='chakra-text SdLEFc2B- css-1jdqp4k',
    cost_class='p',
    cost_link='chakra-text DUXYWqnZ- css-6uvdux'
)

pytorochka = ShopScraper(
    name='Пятерочка',
    link='https://5ka.ru/catalog/73C2330/73C2392/energetiki/?page=1',
    connection_params=pytorochka_connection,
    scraper_config=pytorochka_config,
    website_method='dynamic'
)

# Перекресток
cookies_perekrestok = {...}  # Ваши куки
headers_perekrestok = {...}  # Ваши заголовки

perekrestok_connection = ConnectionParams(
    headers=headers_perekrestok,
    cookies=cookies_perekrestok,
    params=None
)

perekrestok_config = create_shop_config(
    main_class='div',
    main_link='product-card-wrapper',
    name_class='div',
    name_link='product-card__title',
    cost_class='div',
    cost_link='price-new'
)

perekrestok = ShopScraper(
    name='Перекресток',
    link='https://www.perekrestok.ru/cat/c/206/energeticeskie-napitki',
    connection_params=perekrestok_connection,
    scraper_config=perekrestok_config,
    website_method='dynamic'
)