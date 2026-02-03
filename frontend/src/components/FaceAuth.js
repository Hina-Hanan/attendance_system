import React, { useState, useRef, useEffect } from 'react';
import { authenticateFace, punchAttendance } from '../services/api';

const SPOOF_FRAME_COUNT = 5;
const SPOOF_FRAME_INTERVAL_MS = 400;

const FaceAuth = ({ onSuccess }) => {
  const [stream, setStream] = useState(null);
  const [capturedFrames, setCapturedFrames] = useState([]);
  const [capturingStep, setCapturingStep] = useState(null); // null | 1..SPOOF_FRAME_COUNT
  const [authResult, setAuthResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Attach stream to video element after it's in the DOM (ref is set)
  useEffect(() => {
    if (!stream || !videoRef.current) return;
    videoRef.current.srcObject = stream;
    return () => {
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [stream]);

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  const startCamera = async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false
      });
      setStream(mediaStream);
    } catch (err) {
      setError('Failed to access camera. Please allow camera permissions.');
      console.error(err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCapturedFrames([]);
    setCapturingStep(null);
    setAuthResult(null);
  };

  const captureSingleFrame = () => {
    return new Promise((resolve) => {
      if (!videoRef.current || !canvasRef.current) {
        resolve(null);
        return;
      }
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.92);
    });
  };

  const captureAndAuthenticate = async () => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera not ready');
      return;
    }

    setError(null);
    setCapturedFrames([]);

    const frames = [];

    // Capture SPOOF_FRAME_COUNT frames with short delay (allows natural movement)
    for (let i = 0; i < SPOOF_FRAME_COUNT; i++) {
      setCapturingStep(i + 1);
      const blob = await captureSingleFrame();
      if (blob) {
        frames.push(blob);
        setCapturedFrames([...frames]);
      }
      if (i < SPOOF_FRAME_COUNT - 1) {
        await new Promise((r) => setTimeout(r, SPOOF_FRAME_INTERVAL_MS));
      }
    }

    setCapturingStep(null);

    if (frames.length < 3) {
      setError('Could not capture enough frames. Please try again.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await authenticateFace(frames);

      if (response.data.success) {
        setAuthResult(response.data);
      } else {
        setError(response.data.message || 'Authentication failed');
      }
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(
        Array.isArray(d) ? d.map((x) => x?.msg || x).join('. ') : (d || 'Authentication failed')
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePunch = async (action) => {
    if (!authResult || !authResult.user_id) {
      setError('Please authenticate first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await punchAttendance(authResult.user_id, action);
      alert(response.data.message);
      if (onSuccess) {
        onSuccess();
      }
      // Reset after punch
      setAuthResult(null);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x) => x?.msg || x).join('. ') : (d || 'Punch failed'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="section">
      <h2>Face Authentication & Attendance</h2>

      {error && (
        <div className="alert alert-error">{error}</div>
      )}

      {authResult && authResult.success && (
        <div className="alert alert-success">
          <p>Authenticated as: <strong>{authResult.username}</strong></p>
          <p>Confidence: {(authResult.confidence * 100).toFixed(2)}%</p>
          <div style={{ marginTop: '10px' }}>
            <button 
              className="btn btn-success" 
              onClick={() => handlePunch('punch_in')}
              disabled={loading}
            >
              Punch In
            </button>
            <button 
              className="btn btn-danger" 
              onClick={() => handlePunch('punch_out')}
              disabled={loading}
            >
              Punch Out
            </button>
          </div>
        </div>
      )}

      <div className="camera-container">
        {!stream ? (
          <button className="btn btn-primary" onClick={startCamera}>
            Start Camera
          </button>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="video-preview"
              style={{ maxWidth: '640px', width: '100%', background: '#000' }}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            
            <div style={{ marginTop: '10px' }}>
              {capturingStep ? (
                <p style={{ marginBottom: '10px', color: '#666' }}>
                  Capturing for liveness... {capturingStep}/{SPOOF_FRAME_COUNT} (move slightly or blink)
                </p>
              ) : null}
              <button
                className="btn btn-primary capture-button"
                onClick={captureAndAuthenticate}
                disabled={loading || capturingStep !== null}
              >
                {loading
                  ? 'Authenticating...'
                  : capturingStep !== null
                    ? `Capturing ${capturingStep}/${SPOOF_FRAME_COUNT}...`
                    : 'Capture & Authenticate'}
              </button>
              <button className="btn btn-danger" onClick={stopCamera} style={{ marginLeft: '8px' }}>
                Stop Camera
              </button>
            </div>
            <small style={{ color: '#666', display: 'block', marginTop: '8px' }}>
              Captures {SPOOF_FRAME_COUNT} frames for liveness check (helps prevent photos/screens).
            </small>
          </>
        )}
      </div>
    </div>
  );
};

export default FaceAuth;
