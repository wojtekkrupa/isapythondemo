# -*- coding: utf-8 -*-
"""
    Aplikacja do analizy danych za pomocą biblioteki pandas.
"""

import re
import sys
import pandas
import numpy
from plotly import (
   offline,
   graph_objs,
)

VERBOSE_INFO = (
    '#1 w jakich stanach są dostępne laptopy'
    '\n{0}\n\n'
    '#2 ile waży najlżejszy, a ile najcięższy laptop'
    '\n{1}\n\n'
    '#3 ile nowych laptopów ma dysk SSD'
    '\n{2}\n\n'
    '#4 jaki jest najpopularniejszy system operacyjny'
    '\n{3}\n\n'
    '#5 jaką część całości stanowią laptopy o danym stanie'
    '\nFUNKCJA NIE ZAIMPLEMENTOWANA!\n\n'
    '\n'
    '#6 który producent jest dostawcą najpopularniejszych GPU'
    '\n{4}\n\n'
    '#7 jaki jest średni stosunek pojemności RAM do HDD'
    '\nFUNKCJA NIE ZAIMPLEMENTOWANA!\n\n'
    '\n'
    '#8 ile laptopów ma błyszczącą matrycę w rozdzielczości HD lub mniejszej'
    '\n{5}\n\n'
    '#9 w ilu laptopach nie podano typu obsługiwanej pamięci'
    '\n{6}\n\n'
)


class BaseDataModel(object):
    _model = None

    def __init__(self, model):
        self._model = model


class DataDesc(BaseDataModel):
    """
        Model opisujący zdefiniowane cechy kolekcji.
    """
    GFX_MODELS = ('amd', 'intel', 'nvidia')
    HD_X = 1920

    def _get_gfx_chip_provider(self, value):
        """
            Zwraca nazwę producenta procesora graficznego lub obiekt nan.
        """
        if not pandas.isna(value):
            for company in self.GFX_MODELS:
                if company in value.lower():
                    return company
        return numpy.nan

    def _is_hd_resolution(self, value):
        """
            Sprawdza, czy podana wartość jest rozdzielczością HD lub mniejszą
        """
        if not pandas.isna(value):
            return value[0] <= self.HD_X
        return False

    @property
    def available_conditions(self):
        """
            Zwraca zbiór dostępnych stanów laptopów.
        """
        return set(self._model['condition'])

    @property
    def min_max_weight(self):
        """
            Zwraca najmniejszą i największą pojemność baterii.
        """
        return self._model['battery_capacity'].min(), self._model['battery_capacity'].max()

    @property
    def new_with_ssd(self):
        """
            Zwraca liczbę nowych laptopów z dyskami SSD.
        """
        return len(
            self._model[
                (self._model['condition'] == 'Nowy') & (self._model['hdd_type'] == 'SSD')
            ]
        )

    @property
    def most_popular_os(self):
        """
            Zwraca najpopularniejszy system operacyjny w postaci: (nazwa, liczba)
        """
        top_os = self._model.groupby('os').size()
        top_os = top_os.sort_values()[-1:]
        return (top_os.index[0], top_os.values[0])

    @property
    def most_popular_gfx(self):
        """
            Zwraca najpopularniejszego producenta procesorów graficznych.
        """
        gfx_cards = self._model['gfx_type'].apply(self._get_gfx_chip_provider)
        most_popular = gfx_cards.groupby(gfx_cards).size().sort_values()[-1:]
        return most_popular.index[0], most_popular.values[0]

    @property
    def hd_glare_display(self):
        """
            Zwraca liczbę laptopów z błyszącą matrycą w rozdzielczości HD lub mniejszej.
        """
        return len(self._model[
            (self._model['display_surface'] == 'błyszcząca') &
            (self._model['display_resolution'].apply(self._is_hd_resolution))
        ])

    @property
    def no_ram_type_items(self):
        """
            Zwraca ilość laptopów bez podanego typu pamięci.
        """
        return len(self._model[self._model['ram_type'].isna()])

    @property
    def ram2hdd_ratio(self):
        """
            Zwraca stosunek pojemności RAM do HDD.
        """
        raise NotImplementedError

    def _draw_bar_graph(self, labels, values, filename):
        """
            Rysuje wykres słupkowy.
            labels i values to listy wartości.
        """
        data = [
            graph_objs.Bar(
                x=labels,
                y=values,
            )
        ]
        offline.plot(data, filename=filename)

    def _draw_pie_graph(self, labels, values, filename):
        """
            Rysuje wykres słupkowy.
            labels i values to listy wartości.
        """
        data = [
            graph_objs.Pie(
                labels=labels,
                values=values,
            )
        ]
        offline.plot(data, filename=filename)

    def condition_items(self):
        """
            Wykres ilości obiektów o danym stanie.
        """
        data = self._model.groupby('condition').size()
        self._draw_pie_graph(
            list(data.keys()),
            list(data.values),
            'condition_items.html'
        )

    def memory_size(self):
        """
            Wykres pojemności pamięci RAM.
        """
        data = self._model.groupby('ram_size').size()
        self._draw_bar_graph(
            list(data.keys()),
            list(data.values),
            'memory_size.html'
        )


class DataModel(object):
    """
        Model obsługujący obiekt DataFrame.
    """
    data = None
    model = None
    FLOAT_RE = re.compile('\d+\.?\d?')
    MAH_VOLTAGE = 3.7
    MAH_RATIO = 1000

    def __init__(self, file_path):
        self.data = pandas.read_csv(file_path)
        self._normalize_data()
        self.model = DataDesc(self.data)

    def _str2float(self, text):
        """
            Konwertuje literał tekstowy do obiektu float.
            Zwraca nan, jeśli konwersja nie jest możliwa.
        """
        if not pandas.isna(text):
            parsed = re.search(self.FLOAT_RE, text)
            if parsed:
                try:
                    return round(float(parsed.group()), 2)
                except (ValueError, TypeError):
                    pass
        return numpy.nan

    def _str2int(self, text):
        """
            Konwertuje literał tekstowy do obiektu int.
            Zwraca nan, jeśli konwersja nie jest możliwa.
        """
        if not pandas.isna(text):
            parsed = re.search(self.FLOAT_RE, text)
            if parsed:
                try:
                    return int(parsed.group())
                except (ValueError, TypeError):
                    pass
        return numpy.nan

    def _str2res(self, text):
        """
            Normalizuje literał rozdzielczości w formacie `123 x 123`
            do postaci tupli (int(x), int(y)).
            Zwraca nan, jeśli konwercja nie jest możliwa.
        """
        if not pandas.isna(text) and 'x' in text.lower():
            x_res, y_res = text.split('x')
            return (int(x_res.strip()), int(y_res.strip()))
        return numpy.nan

    def _mah2wh(self, text):
        """
            Konwertuje pojemność mAh -> Wh.
            Zwraca float lub nan
        """
        if not pandas.isna(text):
            if 'mah' in text.lower():
                return round(
                    self._str2float(text) * self.MAH_VOLTAGE / self.MAH_RATIO, 2
                )
            elif 'wh' in text.lower():
                return self._str2float(text)
        return numpy.nan

    def _normalize_data(self):
        """
            Normalizuje dane w modelu DataFrame.
        """
        self.data['cpu_speed'] = self.data['cpu_speed'].apply(self._str2float)
        self.data['weight'] = self.data['weight'].apply(self._str2float)
        self.data['ram_size'] = self.data['ram_size'].apply(self._str2int)
        self.data['hdd_size'] = self.data['hdd_size'].apply(self._str2int)
        self.data['display_resolution'] = self.data['display_resolution'].apply(self._str2res)
        self.data['battery_capacity'] = self.data['battery_capacity'].apply(self._mah2wh)

    def print_info(self):
        """
            Wyświetla wyliczone dane.
        """
        print(VERBOSE_INFO.format(
            self.model.available_conditions,
            self.model.min_max_weight,
            self.model.new_with_ssd,
            self.model.most_popular_os,
            self.model.most_popular_gfx,
            self.model.hd_glare_display,
            self.model.no_ram_type_items
        ))


if __name__ == '__main__':
    try:
        file_path = sys.argv[1]
    except IndexError:
        print('Użycie: python {0} plik.csv'.format(__file__))
    else:
        model = DataModel(sys.argv[1])
        print('Dane wczytane z pliku {0}'.format(file_path))
        model.print_info()
        print('Przygotowanie wykresów')
        model.model.condition_items()
        model.model.memory_size()
