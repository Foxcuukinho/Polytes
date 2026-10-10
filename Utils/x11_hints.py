# Utils/x11_hints.py
from Xlib.display import Display
from Xlib import X
import Xlib.Xatom

def set_always_on_top_x11(window_id):

    display = Display()
    root = display.screen().root
    window = display.create_resource_object('window', window_id)

    def atom(name):
        return display.intern_atom(name)

    net_wm_state = atom('_NET_WM_STATE')
    states = [
        atom('_NET_WM_STATE_ABOVE'),
        atom('_NET_WM_STATE_SKIP_TASKBAR'),
        atom('_NET_WM_STATE_SKIP_PAGER'),
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

    def atom(name):
        return display.intern_atom(name)

    net_wm_window_type = atom('_NET_WM_WINDOW_TYPE')
    dock_type = atom('_NET_WM_WINDOW_TYPE_DOCK')

    window.change_property(
        net_wm_window_type,
        Xlib.Xatom.ATOM,
        32,
        [dock_type]
    )

    display.flush()

def protocol_client_message(window, message_type, state_atom):
    from Xlib.protocol import event as xevent

    return xevent.ClientMessage(
        window=window,
        client_type=message_type,
        data=(32, [
            1,  # _NET_WM_STATE_ADD
            state_atom,
            0,
            1,  # source indication: aplicação normal
            0
        ])
    )