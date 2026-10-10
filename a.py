from ewmhlib import EwmhRoot
import pywinctl as pwc

stacking = EwmhRoot().getClientListStacking()
print("stacking:", stacking)
print("tipo:", type(stacking[0]) if stacking else None)

for w in pwc.getAllWindows():
    h = w.getHandle()
    print(w.title, "handle:", h, "tipo:", type(h), "está na stacking?", h in stacking)