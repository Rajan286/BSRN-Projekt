from common_test import pipe_path

def test_pipe_path_generation():
    path = pipe_path("net_to_ui")
    assert path.endswith("net_to_ui.pipe")
    assert "/tmp/slcp_" in path