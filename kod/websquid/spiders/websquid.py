# -*- coding: utf-8 -*-
"""
    Aplikacja pobierająca dane z allegro.
"""

import scrapy
from time import sleep


class WebSquid(scrapy.Spider):
    current_list_count = 0
    max_list_count = 3  # liczba stron do pobrania
    wait_time = 1  # opóźnienie w celu ograniczenia częstotliwości zapytań HTTP
    failsafe_item_count = 100  # maksymalna liczba produktów na stonie (nominalnie spodziewam się 60)

    name = "websquid"
    allowed_domains = ['allegro.pl']
    ITEM_URL_XPATH = '//*[@id="opbox-listing"]/div/div/section[2]/section/article[{0}]/div/div/div[2]/div[1]/h2/a'
    ITEM_DETAILS_XPATH = "//text()[normalize-space() = '{param_name}:']/../following-sibling::div/text()"
    START_URL = 'https://allegro.pl/kategoria/laptopy-491?order=m'
    NEXT_PAGE_CSS = 'a[rel="next"]'
    DETAILS_PARAMS = {
        'condition': 'Stan',
        'display_type': 'Typ matrycy',
        'hdd_type': 'Typ dysku twardego',
        'os': 'System operacyjny',
        'cpu_line': 'Seria procesora',
        'cpu_cores': 'Liczba rdzeni procesora',
        'cpu_speed': 'Taktowanie maksymalne procesora',
        'ram_size': 'Wielkość pamięci RAM',
        'ram_type': 'Typ pamięci RAM',
        'ram_speed': 'Częstotliwość taktowania pamięci (MHz)',
        'hdd_size': 'Pojemność dysku',
        'display_surface': 'Powłoka matrycy',
        'display_resolution': 'Rozdzielczość (px)',
        'gfx_type': 'Model karty graficznej',
        'weight': 'Waga produktu',
        'battery_capacity': 'Pojemność akumulatora'
    }

    def start_requests(self):
        return [scrapy.Request(url=self.START_URL, callback=self.parse_item_list)]

    def parse_item(self, response):
        """
            Parsuje stronę przedmiotu.
            Zwraca słownik atrybutów produktu.
        """
        sleep(self.wait_time)
        details = {}
        for param_name in self.DETAILS_PARAMS:
            details[param_name] = response.xpath(
                self.ITEM_DETAILS_XPATH.format(param_name=self.DETAILS_PARAMS[param_name])
            ).extract_first()
        return details

    def parse_item_list(self, response):
        """
            Parsuje listę wyników.
            Szuka linków do podstron produktów. Gdy zbiór zostanie wyczerpany,
            zwraca kolejną podstronę listingu.
        """
        index = 1
        while index < self.failsafe_item_count:
            item_xpath = response.xpath(self.ITEM_URL_XPATH.format(index))
            if item_xpath:
                yield scrapy.Request(url=item_xpath.attrib['href'], callback=self.parse_item)
            else:
                # podstrona wyników nie ma już więcej elementów,
                # należy przejść na kolejną podstronę
                next_page = response.css(self.NEXT_PAGE_CSS)
                if next_page and self.current_list_count <= self.max_list_count:
                    # jeśli istnieje kolejna podstrona i nie przekroczono liczby podstron
                    self.current_list_count += 1
                    # będą dwa linki przenoszące na następną stronę
                    next_page_url = next_page[0].attrib['href']
                    yield scrapy.Request(url=next_page_url, callback=self.parse_item_list)
                raise StopIteration
            index += 1
