"""
WebSocket Manager for Real-time Communication

Manages WebSocket connections for real-time updates, live conversations,
and streaming data between clients and the Cognitive-Twin system.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
import uuid

try:
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.websockets import WebSocketState
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available. Install with: pip install fastapi websockets")

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections for real-time communication.
    
    Handles connection management, message routing, and real-time updates
    for live interaction with the Cognitive-Twin system.
    """
    
    def __init__(self):
        """Initialize WebSocket manager"""
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not available. Install with: pip install fastapi websockets")
        
        # Active connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        
        # Connection groups for broadcasting
        self.connection_groups: Dict[str, Set[str]] = {}
        
        # Heartbeat management
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info("WebSocket manager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_type: str = "general") -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
            connection_type: Type of connection (general, conversation, analysis)
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Store connection
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connection_type": connection_type,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Start heartbeat
        self.heartbeat_tasks[connection_id] = asyncio.create_task(
            self._heartbeat_loop(connection_id)
        )
        
        # Send welcome message
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "message": "Connected to Cognitive-Twin real-time system",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
        """
        if connection_id in self.active_connections:
            # Cancel heartbeat task
            if connection_id in self.heartbeat_tasks:
                self.heartbeat_tasks[connection_id].cancel()
                del self.heartbeat_tasks[connection_id]
            
            # Remove from groups
            for group_name, connections in self.connection_groups.items():
                connections.discard(connection_id)
            
            # Close connection
            websocket = self.active_connections[connection_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()
            
            # Clean up
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to a specific connection.
        
        Args:
            connection_id: Connection ID
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        if connection_id not in self.active_connections:
            return False
        
        websocket = self.active_connections[connection_id]
        
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_activity"] = datetime.utcnow().isoformat()
                
                return True
            else:
                # Connection is closed, clean up
                await self.disconnect(connection_id)
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send message to all connections for a user.
        
        Args:
            user_id: User identifier
            message: Message to send
            
        Returns:
            Number of connections the message was sent to
        """
        sent_count = 0
        
        for connection_id, metadata in self.connection_metadata.items():
            if metadata["user_id"] == user_id:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_to_group(self, group_name: str, message: Dict[str, Any]) -> int:
        """
        Broadcast message to all connections in a group.
        
        Args:
            group_name: Group name
            message: Message to broadcast
            
        Returns:
            Number of connections the message was sent to
        """
        if group_name not in self.connection_groups:
            return 0
        
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in self.connection_groups[group_name].copy():
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            self.connection_groups[group_name].discard(connection_id)
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """
        Broadcast message to all active connections.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Number of connections the message was sent to
        """
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in list(self.active_connections.keys()):
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up failed connections
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return sent_count
    
    def add_to_group(self, connection_id: str, group_name: str):
        """
        Add connection to a group.
        
        Args:
            connection_id: Connection ID
            group_name: Group name
        """
        if group_name not in self.connection_groups:
            self.connection_groups[group_name] = set()
        
        self.connection_groups[group_name].add(connection_id)
        logger.info(f"Connection {connection_id} added to group {group_name}")
    
    def remove_from_group(self, connection_id: str, group_name: str):
        """
        Remove connection from a group.
        
        Args:
            connection_id: Connection ID
            group_name: Group name
        """
        if group_name in self.connection_groups:
            self.connection_groups[group_name].discard(connection_id)
            logger.info(f"Connection {connection_id} removed from group {group_name}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """
        Register a message handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered message handler for type: {message_type}")
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """
        Handle incoming message from a connection.
        
        Args:
            connection_id: Connection ID
            message: Message data
        """
        message_type = message.get("type")
        
        if not message_type:
            await self.send_to_connection(connection_id, {
                "type": "error",
                "message": "Message type is required",
                "timestamp": datetime.utcnow().isoformat()
            })
            return
        
        # Update last activity
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_activity"] = datetime.utcnow().isoformat()
        
        # Call registered handler
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](connection_id, message)
            except Exception as e:
                logger.error(f"Error in message handler for {message_type}: {e}")
                await self.send_to_connection(connection_id, {
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        else:
            # Default handler
            await self._default_message_handler(connection_id, message)
    
    async def _default_message_handler(self, connection_id: str, message: Dict[str, Any]):
        """Default message handler for unhandled message types"""
        await self.send_to_connection(connection_id, {
            "type": "message_received",
            "original_type": message.get("type"),
            "message": "Message received but no specific handler found",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _heartbeat_loop(self, connection_id: str):
        """Heartbeat loop to keep connection alive and detect disconnections"""
        while connection_id in self.active_connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if connection_id in self.active_connections:
                    # Send ping
                    await self.send_to_connection(connection_id, {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Wait for pong
                    await asyncio.sleep(5)
                    
                    # Check if connection is still active
                    if connection_id in self.connection_metadata:
                        last_activity = self.connection_metadata[connection_id]["last_activity"]
                        last_activity_time = datetime.fromisoformat(last_activity)
                        
                        # If no activity for 2 minutes, disconnect
                        if (datetime.utcnow() - last_activity_time).total_seconds() > 120:
                            logger.warning(f"Connection {connection_id} timed out")
                            await self.disconnect(connection_id)
                            break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {connection_id}: {e}")
                await self.disconnect(connection_id)
                break
    
    async def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Connection information or None
        """
        if connection_id not in self.active_connections:
            return None
        
        metadata = self.connection_metadata.get(connection_id, {})
        
        return {
            "connection_id": connection_id,
            "user_id": metadata.get("user_id"),
            "connection_type": metadata.get("connection_type"),
            "connected_at": metadata.get("connected_at"),
            "last_activity": metadata.get("last_activity"),
            "is_active": connection_id in self.active_connections
        }
    
    async def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all connections for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of connection information
        """
        connections = []
        
        for connection_id, metadata in self.connection_metadata.items():
            if metadata["user_id"] == user_id:
                connection_info = await self.get_connection_info(connection_id)
                if connection_info:
                    connections.append(connection_info)
        
        return connections
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Connection statistics
        """
        total_connections = len(self.active_connections)
        
        # Count by connection type
        type_counts = {}
        for metadata in self.connection_metadata.values():
            conn_type = metadata.get("connection_type", "unknown")
            type_counts[conn_type] = type_counts.get(conn_type, 0) + 1
        
        # Count by user
        user_counts = {}
        for metadata in self.connection_metadata.values():
            user_id = metadata.get("user_id", "unknown")
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        # Group statistics
        group_stats = {}
        for group_name, connections in self.connection_groups.items():
            group_stats[group_name] = len(connections)
        
        return {
            "total_connections": total_connections,
            "connections_by_type": type_counts,
            "connections_by_user": user_counts,
            "group_statistics": group_stats,
            "active_heartbeats": len(self.heartbeat_tasks),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup_inactive_connections(self):
        """Clean up inactive connections"""
        inactive_connections = []
        
        for connection_id, metadata in self.connection_metadata.items():
            last_activity = metadata.get("last_activity")
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                # Disconnect if inactive for more than 5 minutes
                if (datetime.utcnow() - last_activity_time).total_seconds() > 300:
                    inactive_connections.append(connection_id)
        
        for connection_id in inactive_connections:
            logger.info(f"Cleaning up inactive connection: {connection_id}")
            await self.disconnect(connection_id)
        
        return len(inactive_connections)
