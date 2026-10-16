import sys

IS_LINUX = sys.platform.startswith("linux")

if IS_LINUX:
    try:
        from Xlib.display import Display
        from Xlib import X
        import Xlib.Xatom
        from Xlib.protocol import event as xevent
    except ImportError:
        IS_LINUX = False  # Linux, mas sem python-xlib instalado

    def protocol_client_message(window, message_type, state_atom):
        return xevent.ClientMessage(
            window=window,
            client_type=message_type,
            data=(32, [1, state_atom, 0, 1, 0])
        )

    def set_always_on_top_x11(window_id):
        display = Display()
        root = display.screen().root
        window = display.create_resource_object('window', window_id)

        net_wm_state = display.intern_atom('_NET_WM_STATE')
        states = [
            display.intern_atom('_NET_WM_STATE_ABOVE'),
            display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
            display.intern_atom('_NET_WM_STATE_SKIP_PAGER'),
        ]

        for state in states:
            event = protocol_client_message(window, net_wm_state, state)
            root.send_event(
                event,
                event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask
            )
        display.flush()

    def set_window_type_dock(window_id):
        display = Display()
        window = display.create_resource_object('window', window_id)

        window.change_property(
            display.intern_atom('_NET_WM_WINDOW_TYPE'),
            Xlib.Xatom.ATOM,
            32,
            [display.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')]
        )
        display.flush()

else:
    # On other operating systems, these functions exist but do nothing.
    def set_always_on_top_x11(window_id):
        pass

    def set_window_type_dock(window_id):
        pass