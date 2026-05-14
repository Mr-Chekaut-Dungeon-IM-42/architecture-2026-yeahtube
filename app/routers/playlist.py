from fastapi import APIRouter, status, Body
from app.db.session import DBDep

from app.cqs.commands import CreatePlaylistCommand, DeletePlaylistCommand, UpdatePlaylistCommand
from app.cqs.handlers import (
    CreatePlaylistCommandHandler,
    DeletePlaylistCommandHandler,
    PlaylistQueryHandler,
    UpdatePlaylistCommandHandler,
)
from app.cqs.queries import GetPlaylistQuery, GetUserPlaylistsQuery

router = APIRouter(tags=["playlist"], prefix="/playlist")

@router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def create_playlist(user_id: int, db: DBDep, name: str = Body(..., embed=True)):
    playlist_id = CreatePlaylistCommandHandler(db).handle(
        CreatePlaylistCommand(user_id=user_id, name=name)
    )
    return PlaylistQueryHandler(db).handle_get_playlist(
        GetPlaylistQuery(user_id=user_id, playlist_id=playlist_id)
    )

@router.get("/{user_id}")
async def read_user_playlists(user_id: int, db: DBDep):
    return PlaylistQueryHandler(db).handle_user_playlists(GetUserPlaylistsQuery(user_id=user_id))

@router.get("/{user_id}/{playlist_id}")
async def read_playlist(user_id: int, playlist_id: int, db: DBDep):
    return PlaylistQueryHandler(db).handle_get_playlist(
        GetPlaylistQuery(user_id=user_id, playlist_id=playlist_id)
    )

@router.put("/{user_id}/{playlist_id}")
async def update_playlist(user_id: int, playlist_id: int, db: DBDep, name: str = Body(..., embed=True)):
    UpdatePlaylistCommandHandler(db).handle(
        UpdatePlaylistCommand(user_id=user_id, playlist_id=playlist_id, name=name)
    )
    return PlaylistQueryHandler(db).handle_get_playlist(
        GetPlaylistQuery(user_id=user_id, playlist_id=playlist_id)
    )

@router.delete("/{user_id}/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(user_id: int, playlist_id: int, db: DBDep):
    DeletePlaylistCommandHandler(db).handle(
        DeletePlaylistCommand(user_id=user_id, playlist_id=playlist_id)
    )
    return None