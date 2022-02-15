#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 23.12.2021 9:38
"""
version_info = (0, 8)
__title__ = 'Парсер резюме Rabota.ua | Логистика Fozzy Group'
__description__ = 'Офис прогнозирования\nДепартамент мастер данных и отчетности'
__version__ = '.'.join(map(str, version_info))
__author__ = 'Vitaliy Zubriichuk'
__license__ = 'MIT License'
__copyright__ = 'Copyright 2022 Zubriichuk Vitaliy'


def about():
    print(50 * '*')
    print(__title__)
    print('')
    print(__description__)
    print(f'Версия: {__version__}')
    print(50 * '*')
    print('')
