import inspect
from aos.core.security.auth import get_current_operator
print(inspect.signature(get_current_operator))
