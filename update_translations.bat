set TS_FILES=translations\xnovacmd_ru.ts

set SOURCES=app.py ^
 ui\flights_widget.py ^
 ui\flights_widget.ui ^
 ui\galaxy_widget.py ^
 ui\imperium_widget.py ^
 ui\login_widget.py ^
 ui\login_widget.ui ^
 ui\main.py ^
 ui\overview_accstats.ui ^
 ui\overview_widget.py ^
 ui\planet_widget.py ^
 ui\planets_bar_widget.py ^
 ui\settings_widget.py ^
 ui\statusbar.py ^
 ui\widget_utils.py ^
 ui\customwidgets\collapsible_frame.py ^
 ui\customwidgets\my_buttons.py ^
 ui\customwidgets\xtabwidget.py ^
 ui\xnova\xn_world.py

pylupdate5 %SOURCES% -ts %TS_FILES% -verbose
lrelease %TS_FILES%

echo You need to call lrelease %TS_FILES% manually after translations

pause