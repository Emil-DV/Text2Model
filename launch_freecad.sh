#!/bin/bash
# Launch FreeCAD GUI with OpenGL enabled (some shells set QT_XCB_GL_INTEGRATION=none).
unset QT_XCB_GL_INTEGRATION
exec /snap/bin/freecad "$@"
