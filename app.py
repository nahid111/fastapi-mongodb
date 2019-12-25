import uvicorn
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from pydantic import BaseModel

# connect to mongodb
DB_CLIENT = AsyncIOMotorClient('127.0.0.1', 27017)
DB = DB_CLIENT['item_db']

# instantiate app
app = FastAPI(title="Item Store", version="0.1")


class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


def fix_item_id(item):
    if item.get("_id", False):
        item["_id"] = str(item["_id"])
        return item
    else:
        raise ValueError(
            f"No `_id` found! Unable to fix item ID for item: {item}")


# Get item by id
@app.get("/items/{id_}", tags=["items"])
async def read_item(id_: str):
    """[summary]
    Get one item by ID.

    [description]
    Endpoint to retrieve an specific item.
    """
    the_item = await DB.item.find_one({"_id": ObjectId(id_)})
    if the_item:
        return fix_item_id(the_item)
    else:
        raise HTTPException(status_code=404, detail="Item not found")


# Get all items
@app.get("/items/", tags=["items"])
async def get_all_items(limit: int = 0, skip: int = 0):
    # items_cursor = DB.item.find().skip(skip).limit(limit)
    # items = await items_cursor.to_list(length=limit)
    if limit > 0:
        n = limit
    else:
        n = await DB.item.count_documents({})
    items_cursor = DB.item.find()
    items = await items_cursor.to_list(n)
    return list(map(fix_item_id, items))


# Create item
@app.post("/items/", tags=["items"])
async def create_item(item: Item):
    result = await DB.item.insert_one(item.dict())
    the_item = await DB.item.find_one({"_id": result.inserted_id})
    return fix_item_id(the_item)


# Delete item by id
@app.delete("/items/{id_}", tags=["items"])
async def delete_item(id_: str):
    item_op = await DB.item.delete_one({"_id": ObjectId(id_)})
    if item_op.deleted_count:
        return {"status": f"deleted count: {item_op.deleted_count}"}


# Update item by id
@app.put("/items/{id_}", tags=["items"])
async def update_item(id_: str, item_data: Item):
    id_ = ObjectId(id_)
    item_op = await DB.item.update_one(
        {"_id": id_}, {"$set": item_data.dict()}
    )
    if item_op.modified_count:
        item = await DB.item.find_one({"_id": id_})
        return fix_item_id(item)
    else:
        raise HTTPException(status_code=304)


@app.on_event("startup")
async def app_startup():
    print('\nApi running...\n')


@app.on_event("shutdown")
async def app_shutdown():
    # close connection to DB
    DB_CLIENT.close()


if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host='0.0.0.0',
        port=5000,
        reload=True
    )
