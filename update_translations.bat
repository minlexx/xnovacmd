set TS_FILES=translations\xnovacmd_ru.ts

set SOURCES=app.py ui\main.py ui\login_widget.ui ui\login_widget.py ^
 ui\overview.py ui\overview.py ui\flights_widget.ui ui\flights_widget.py ^
 ui\customwidgets\planets_bar_widget.py ui\statusbar.py ui\widget_utils.py ^
 ui\imperium_widget.py ui\xnova\xn_world.py ui\settings_widget.py

pylupdate5 %SOURCES% -ts %TS_FILES% -verbose
lrelease %TS_FILES%

echo You need to call lrelease %TS_FILES% manually after translations

pause