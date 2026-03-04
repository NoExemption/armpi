#!/bin/sh

if [ -n "$DESTDIR" ] ; then
    case $DESTDIR in
        /*) # ok
            ;;
        *)
            /bin/echo "DESTDIR argument must be absolute... "
            /bin/echo "otherwise python's distutils will bork things."
            exit 1
    esac
fi

echo_and_run() { echo "+ $@" ; "$@" ; }

echo_and_run cd "/home/rosnoetic/armpi/src/easy_handeye/easy_handeye"

# ensure that Python install destination exists
echo_and_run mkdir -p "$DESTDIR/home/rosnoetic/armpi/install/lib/python3/dist-packages"

# Note that PYTHONPATH is pulled from the environment to support installing
# into one location when some dependencies were installed in another
# location, #123.
echo_and_run /usr/bin/env \
    PYTHONPATH="/home/rosnoetic/armpi/install/lib/python3/dist-packages:/home/rosnoetic/armpi/build/lib/python3/dist-packages:$PYTHONPATH" \
    CATKIN_BINARY_DIR="/home/rosnoetic/armpi/build" \
    "/usr/bin/python3" \
    "/home/rosnoetic/armpi/src/easy_handeye/easy_handeye/setup.py" \
    egg_info --egg-base /home/rosnoetic/armpi/build/easy_handeye/easy_handeye \
    build --build-base "/home/rosnoetic/armpi/build/easy_handeye/easy_handeye" \
    install \
    --root="${DESTDIR-/}" \
    --install-layout=deb --prefix="/home/rosnoetic/armpi/install" --install-scripts="/home/rosnoetic/armpi/install/bin"
