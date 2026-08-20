from cv_service.processing import detect_faces_in_frame


def test_garbled_frame_is_handled_and_logged(caplog):
    with caplog.at_level("WARNING"):
        result = detect_faces_in_frame(b"not-a-real-image")

    assert result is None
    assert "Unable to decode video frame" in caplog.text


def test_missing_frame_is_handled_and_logged(caplog):
    with caplog.at_level("WARNING"):
        result = detect_faces_in_frame()

    assert result is None
    assert "No frame bytes or frame path provided" in caplog.text


def test_invalid_file_path_is_handled_and_logged(caplog):
    with caplog.at_level("WARNING"):
        result = detect_faces_in_frame(
            frame_path="/tmp/this-file-does-not-exist.jpg"
        )

    assert result is None
    assert "Unable to decode video frame" in caplog.text
