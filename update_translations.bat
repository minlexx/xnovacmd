set TS_FILES=translations\xnovacmd_ru.ts

set SOURCES=app.py ui\main.ui ui\main.py ui\login_widget.ui ui\login_widget.py ui\overview.py ui\overview.py ui\flights_widget.ui ui\flights_widget.py ui\planets_panel.py ui\statusbar.py ui\widget_utils.py

pylupdate5 %SOURCES% -ts %TS_FILE% -verbose
pause