import React, { useState, useRef, useEffect } from 'react';
import { registerUser } from '../services/api';

/**
 * Format API error detail for display.
 * FastAPI can return detail as string or array of { type, loc, msg, input }.
 */
function formatErrorDetail(detail) {
  if (detail == null) return 'Registration failed';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (d && d.msg) ? d.msg : JSON.stringify(d)).join('. ');
  }
  if (typeof detail === 'object' && detail.msg) return detail.msg;
  return String(detail);
}

const UserRegistration = ({ onSuccess }) => {
  const [username, setUsername] = useState('');
  const [inputMethod, setInputMethod] = useState('upload'); // 'upload' | 'capture'
  const [files, setFiles] = useState([]);
  const [capturedBlobs, setCapturedBlobs] = useState([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length < 3 || selectedFiles.length > 4) {
      setError('Please select 3-4 face images');
      return;
    }
    setFiles(selectedFiles);
    setError(null);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      streamRef.current = stream;
      setCameraActive(true);
      setError(null);
    } catch (err) {
      setError('Could not access camera. Please allow camera permissions.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraActive(false);
    setCapturedBlobs([]);
  };

  useEffect(() => {
    if (cameraActive && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [cameraActive]);

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        setCapturedBlobs((prev) => {
          const next = [...prev, blob];
          if (next.length > 4) return prev;
          return next;
        });
      },
      'image/jpeg',
      0.92
    );
  };

  const removeCaptured = (index) => {
    setCapturedBlobs((prev) => prev.filter((_, i) => i !== index));
  };

  const getFilesToSubmit = () => {
    if (inputMethod === 'upload') return files;
    return capturedBlobs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username.trim()) {
      setError('Please enter a username');
      return;
    }

    const toSubmit = getFilesToSubmit();
    if (toSubmit.length < 3 || toSubmit.length > 4) {
      setError(inputMethod === 'upload'
        ? 'Please select 3-4 face images'
        : 'Please capture 3-4 face images with the webcam');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await registerUser(username, toSubmit);
      setSuccess(
        response.data.user_number != null
          ? `User ${response.data.username} registered successfully! Your User ID (number) is: ${response.data.user_number}. Save this number to identify yourself in the attendance chart.`
          : `User ${response.data.username} registered successfully! User ID: ${response.data.user_id}`
      );
      setUsername('');
      setFiles([]);
      setCapturedBlobs([]);
      stopCamera();
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(formatErrorDetail(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  const filesOrCaptured = getFilesToSubmit();
  const canSubmit = filesOrCaptured.length >= 3 && filesOrCaptured.length <= 4 && username.trim();

  return (
    <div className="section">
      <h2>Register New User</h2>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {success && (
        <div className="alert alert-success">{success}</div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username *</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            required
          />
        </div>

        <div className="form-group">
          <label>Face images: choose method</label>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input
                type="radio"
                name="inputMethod"
                checked={inputMethod === 'upload'}
                onChange={() => { setInputMethod('upload'); setError(null); setCapturedBlobs([]); stopCamera(); }}
              />
              Upload images
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input
                type="radio"
                name="inputMethod"
                checked={inputMethod === 'capture'}
                onChange={() => { setInputMethod('capture'); setError(null); setFiles([]); }}
              />
              Capture with webcam
            </label>
          </div>

          {inputMethod === 'upload' && (
            <>
              <input
                type="file"
                id="face-images"
                accept="image/*"
                multiple
                onChange={handleFileChange}
              />
              {files.length > 0 && (
                <div className="file-input-container" style={{ marginTop: '10px' }}>
                  {files.map((file, index) => (
                    <div key={index} className="file-input-item">
                      <span>{file.name}</span>
                    </div>
                  ))}
                </div>
              )}
              <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                Upload 3-4 clear face images from different angles.
              </small>
            </>
          )}

          {inputMethod === 'capture' && (
            <div className="camera-container">
              {!cameraActive ? (
                <button type="button" className="btn btn-primary" onClick={startCamera}>
                  Start camera
                </button>
              ) : (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="video-preview"
                    style={{ maxWidth: '100%', width: '400px', borderRadius: '8px' }}
                  />
                  <canvas ref={canvasRef} style={{ display: 'none' }} />
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button type="button" className="btn btn-secondary" onClick={captureImage} disabled={loading}>
                      Capture image ({capturedBlobs.length}/4)
                    </button>
                    <button type="button" className="btn btn-danger" onClick={stopCamera}>
                      Stop camera
                    </button>
                  </div>
                  {capturedBlobs.length > 0 && (
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
                      {capturedBlobs.map((blob, index) => (
                        <div key={index} style={{ position: 'relative' }}>
                          <img
                            src={URL.createObjectURL(blob)}
                            alt={`Capture ${index + 1}`}
                            style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '6px' }}
                          />
                          <button
                            type="button"
                            onClick={() => removeCaptured(index)}
                            style={{
                              position: 'absolute',
                              top: '-4px',
                              right: '-4px',
                              background: '#dc3545',
                              color: 'white',
                              border: 'none',
                              borderRadius: '50%',
                              width: '20px',
                              height: '20px',
                              cursor: 'pointer',
                              fontSize: '12px',
                              lineHeight: 1
                            }}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <small style={{ color: '#666', display: 'block', marginTop: '8px' }}>
                    Capture 3-4 images from slightly different angles.
                  </small>
                </>
              )}
            </div>
          )}
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !canSubmit}
        >
          {loading ? 'Registering...' : 'Register User'}
        </button>
      </form>
    </div>
  );
};

export default UserRegistration;
