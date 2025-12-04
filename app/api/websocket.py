"""
WebSocket API endpoint for real-time notifications
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.services.websocket_manager import websocket_manager
from app.core.exceptions import AuthenticationException
from app.core.jwt_utils import verify_token
from app.services.user_service import get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


async def authenticate_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Optional[Session] = None
) -> dict:
    """Authenticate WebSocket connection using JWT token (v2 - local PostgreSQL)"""
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        raise AuthenticationException(
            user_message="Authentication token required",
            technical_message="No token provided in WebSocket connection"
        )
    
    try:
        # Verify JWT token
        payload = verify_token(token)
        
        # Extract user info from token
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        
        # Verify user still exists in database
        user = get_user_by_id(user_id, db)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            raise AuthenticationException(
                user_message="Invalid authentication token",
                technical_message=f"User {user_id} not found in database"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        await websocket.close(code=1008, reason="Authentication failed")
        raise AuthenticationException(
            user_message="Authentication failed",
            technical_message=f"WebSocket authentication error: {str(e)}"
        )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time notifications"""
    user = None
    
    try:
        # Get database session for authentication
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            # Authenticate connection
            user = await authenticate_websocket(websocket, token, db)
            user_id = user["id"]
            user_email = user["email"]
        finally:
            db.close()
        
        # Connect
        await websocket_manager.connect(websocket, user_id, user_email)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }, user_id)
                    continue
                
                action = message.get("action")
                
                if action == "subscribe":
                    resource_type = message.get("resource_type")
                    resource_id = message.get("resource_id")
                    
                    if not resource_type or resource_id is None:
                        await websocket_manager.send_personal_message({
                            "type": "error",
                            "message": "Missing resource_type or resource_id"
                        }, user_id)
                        continue
                    
                    await websocket_manager.subscribe(user_id, resource_type, resource_id)
                
                elif action == "unsubscribe":
                    resource_type = message.get("resource_type")
                    resource_id = message.get("resource_id")
                    
                    if not resource_type or resource_id is None:
                        await websocket_manager.send_personal_message({
                            "type": "error",
                            "message": "Missing resource_type or resource_id"
                        }, user_id)
                        continue
                    
                    await websocket_manager.unsubscribe(user_id, resource_type, resource_id)
                
                elif action == "ping":
                    # Keep-alive ping
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, user_id)
                
                else:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    }, user_id)
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Error processing message"
                }, user_id)
    
    except AuthenticationException:
        # Already handled, connection closed
        pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user.get('id') if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Clean up on disconnect
        if user:
            websocket_manager.disconnect(user["id"])

