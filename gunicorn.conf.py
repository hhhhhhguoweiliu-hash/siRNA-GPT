"""Small startup smoke check in the actual deployed runtime (one worker only)."""
def post_worker_init(worker):
    import threading
    from startup_checks import run
    threading.Thread(target=run, daemon=True, name='deployment-check').start()
