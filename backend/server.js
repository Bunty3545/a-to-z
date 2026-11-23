/**
 * Real-Time Activity Auditing & Telemetry Server
 * Built with Node.js, Express, and Socket.io
 */

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const path = require('path');

const app = express();
const server = http.createServer(app);

// Enable CORS for client applications & dashboards
app.use(cors({ origin: '*' }));
app.use(express.json());

// Setup Socket.io for bi-directional real-time event streaming
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

const PORT = process.env.PORT || 4000;
const AUTH_SECRET = process.env.ADMIN_SECRET || 'uni-audit-secret-token-2026';

// Circular buffer for in-memory audit history (last 500 events)
const MAX_HISTORY = 500;
const auditHistory = [];

// Real-time access control map: tracks activation status and execution state per user
const userControlMap = {
  "12303979": { status: "ACTIVE", state: "RUNNING" },
  "12303980": { status: "ACTIVE", state: "RUNNING" }
};

// Middleware: Authenticate incoming client telemetry requests
function authenticateClient(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader) {
    return res.status(401).json({ success: false, message: 'Missing Authorization header' });
  }

  const token = authHeader.replace(/^Bearer\s+/i, '').trim();
  // Simple bearer token validation (can be replaced with JWT verify)
  if (token !== AUTH_SECRET && !token.startsWith('user_access_')) {
    return res.status(403).json({ success: false, message: 'Invalid or expired access token' });
  }

  req.userToken = token;
  next();
}

// -------------------------------------------------------------
// REST API ROUTES
// -------------------------------------------------------------

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    timestamp: new Date().toISOString(),
    connectedAdmins: io.engine.clientsCount,
    totalLoggedEvents: auditHistory.length
  });
});

// Retrieve recent audit history for newly opened admin dashboards
app.get('/api/events', (req, res) => {
  const limit = Math.min(parseInt(req.query.limit, 10) || 100, 500);
  res.json({
    success: true,
    count: auditHistory.length,
    events: auditHistory.slice(-limit)
  });
});

// Event Ingestion Endpoint: Called whenever a client performs an audited action
app.post('/api/events', authenticateClient, (req, res) => {
  const { userId, userName, action, status, details, timestamp } = req.body;

  if (!userId || !action) {
    return res.status(400).json({
      success: false,
      message: 'Payload must contain userId and action'
    });
  }

  // Construct structured audit record
  const eventRecord = {
    id: `ev_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    timestamp: timestamp || new Date().toISOString(),
    reg_no: String(userId),
    user_name: userName || 'Authenticated User',
    session_id: req.body.sessionId || 'session_' + Math.random().toString(16).substring(2, 8),
    action: String(action).toUpperCase(),
    status: status || 'SUCCESS',
    details: details || {}
  };

  // Push to circular history buffer
  auditHistory.push(eventRecord);
  if (auditHistory.length > MAX_HISTORY) {
    auditHistory.shift();
  }

  // Real-time broadcast to all connected admin dashboard sockets
  io.emit('new_audit_event', eventRecord);

  console.log(`[AUDIT] [${eventRecord.timestamp}] User: ${eventRecord.reg_no} | Action: ${eventRecord.action}`);

  return res.status(201).json({
    success: true,
    message: 'Event logged and streamed to admin dashboard',
    eventId: eventRecord.id
  });
});

// Access Control endpoint: Admin can Pause/Resume or Deactivate/Activate user
app.post('/api/control', (req, res) => {
  const { regNo, command, adminName } = req.body;
  if (!regNo || !command) {
    return res.status(400).json({ success: false, message: 'regNo and command required' });
  }

  if (!userControlMap[regNo]) {
    userControlMap[regNo] = { status: 'ACTIVE', state: 'RUNNING' };
  }

  if (command === 'PAUSE') userControlMap[regNo].state = 'PAUSED';
  else if (command === 'RESUME') userControlMap[regNo].state = 'RUNNING';
  else if (command === 'DEACTIVATE') userControlMap[regNo].status = 'DEACTIVATED';
  else if (command === 'ACTIVATE') userControlMap[regNo].status = 'ACTIVE';

  const controlEvent = {
    id: `ctrl_${Date.now()}`,
    timestamp: new Date().toISOString(),
    reg_no: String(regNo),
    user_name: 'Admin Console',
    session_id: 'admin_action',
    action: `ADMIN_COMMAND: ${command}`,
    status: command === 'DEACTIVATE' ? 'TERMINATED' : (command === 'PAUSE' ? 'WARNING' : 'SUCCESS'),
    details: { command, targetUser: regNo, issuer: adminName || 'Admin' }
  };

  auditHistory.push(controlEvent);
  io.emit('new_audit_event', controlEvent);
  io.emit('session_control_update', { regNo, ...userControlMap[regNo] });

  console.log(`[CONTROL] Command: ${command} executed for User: ${regNo}`);
  return res.json({ success: true, userState: userControlMap[regNo] });
});

// Query user control status (for client app polling/sync)
app.get('/api/control/:regNo', (req, res) => {
  const regNo = req.params.regNo;
  const state = userControlMap[regNo] || { status: 'ACTIVE', state: 'RUNNING' };
  res.json({ success: true, regNo, ...state });
});

// -------------------------------------------------------------
// WEBSOCKET (SOCKET.IO) MANAGEMENT
// -------------------------------------------------------------
io.on('connection', (socket) => {
  console.log(`[SOCKET] Admin dashboard connected: ${socket.id}`);

  // Send current backlog immediately upon connection
  socket.emit('initial_history', auditHistory.slice(-50));
  socket.emit('initial_controls', userControlMap);

  socket.on('admin_session_control', (data) => {
    const { regNo, command } = data;
    if (regNo && command) {
      if (!userControlMap[regNo]) userControlMap[regNo] = { status: 'ACTIVE', state: 'RUNNING' };
      if (command === 'PAUSE') userControlMap[regNo].state = 'PAUSED';
      else if (command === 'RESUME') userControlMap[regNo].state = 'RUNNING';
      else if (command === 'DEACTIVATE') userControlMap[regNo].status = 'DEACTIVATED';
      else if (command === 'ACTIVATE') userControlMap[regNo].status = 'ACTIVE';

      const controlEvent = {
        id: `ctrl_${Date.now()}`,
        timestamp: new Date().toISOString(),
        reg_no: String(regNo),
        user_name: 'Admin Console',
        session_id: 'admin_action',
        action: `ADMIN_COMMAND: ${command}`,
        status: command === 'DEACTIVATE' ? 'TERMINATED' : (command === 'PAUSE' ? 'WARNING' : 'SUCCESS'),
        details: { command, targetUser: regNo }
      };

      auditHistory.push(controlEvent);
      io.emit('new_audit_event', controlEvent);
      io.emit('session_control_update', { regNo, ...userControlMap[regNo] });
    }
  });

  socket.on('disconnect', () => {
    console.log(`[SOCKET] Admin dashboard disconnected: ${socket.id}`);
  });
});

// Start Server
server.listen(PORT, () => {
  console.log('====================================================');
  console.log(`🚀 Audit Telemetry Backend running on port ${PORT}`);
  console.log(`📡 WebSocket ready for live admin dashboard connections`);
  console.log(`🔐 Authorization Token: Bearer ${AUTH_SECRET}`);
  console.log('====================================================');
});

