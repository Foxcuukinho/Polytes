# Utils/x11_hints.py
from Xlib.display import Display
from Xlib import X
import Xlib.Xatom

def set_always_on_top_x11(window_id):
    """
    Seta hints EWMH via Xlib pra fazer a janela:
    - ficar sempre acima (_NET_WM_STATE_ABOVE)
    - sumir da taskbar (_NET_WM_STATE_SKIP_TASKBAR)
    - sumir do pager/overview (_NET_WM_STATE_SKIP_PAGER)

    window_id: int, geralmente vindo de widget.winId() do Qt (precisa
    ser convertido pra int; no PyQt5 costuma vir como sip.voidptr).
    """
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

    # Manda como ClientMessage pro root, é assim que o EWMH espera
    # (setar a propriedade direto na janela nem sempre é respeitado
    # depois que ela já foi mapeada).
    for state in states:
        event = protocol_client_message(window, net_wm_state, state)
        root.send_event(
            event,
            event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask
        )

    display.flush()

def set_window_type_dock(window_id):
    """
    Declara a janela como DOCK (tipo painel/doca) em vez de NORMAL.
    Isso faz o WM não escondê-la no "mostrar área de trabalho" (Win+D),
    já que DOCK não é considerado "janela de aplicação".

    Precisa ser chamado ANTES do show() — diferente do
    set_always_on_top_x11, que precisa ser depois.
    """
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