    START_PAGE = 'https://allegro.pl/kategoria/laptopy-491'
    XPATH_ITEM_URL = '//*[@id="opbox-listing"]/div/div/section[2]/section/article[{0}]/div/div/div[2]/div[1]/h2/a'
    CSS_NEXT_PAGE = 'a[rel="next"]'
    XPATH_DETAILS = "//text()[normalize-space() = '{param_name}:']/../following-sibling::div/text()"
    max_item_limit = 3
    params = {
        'condition': 'Stan',
        'display_type': 'Typ matrycy',
        'hdd_type': 'Typ dysku twardego',
        'os': 'System operacyjny',
    }