#!/bin/bash
TS_FILES="translations/xnovacmd_ru.ts"

SOURCES="app.py \
    ui/main.ui \
    ui/main.py \
    ui/login_widget.ui \
    ui/login_widget.py \
    ui/overview.py \
    ui/overview.py \
    ui/flights_widget.ui \
    ui/flights_widget.py \
    ui/customwidgets/planets_bar_widget.py \
    ui/statusbar.py \
    ui/widget_utils.py \
    ui/imperium.py"

echo "TS files: $TS_FILES"
echo "Sources: $SOURCES"

pylupdate5 $SOURCES -ts $TS_FILES -verbose
lrelease $TS_FILES

echo "You need to call lrelease $TS_FILES manually after translations"
