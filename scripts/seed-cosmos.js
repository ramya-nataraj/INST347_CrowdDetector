// Loads data/mock-data.json into Azure Cosmos DB.
// Run: node scripts/seed-cosmos.js
// Needs COSMOS_CONNECTION_STRING in a local .env file (get it from Ramya). NEVER commit .env.
require("dotenv").config();
const { CosmosClient } = require("@azure/cosmos");
const data = require("../data/mock-data.json");

const DB_NAME = "crowddetector";

async function main() {
  const conn = process.env.COSMOS_CONNECTION_STRING;
  if (!conn) throw new Error("Missing COSMOS_CONNECTION_STRING in .env");

  const client = new CosmosClient(conn);
  const { database } = await client.databases.createIfNotExists({ id: DB_NAME });

  // Partition keys: stores by /id, readings by /storeId
  const { container: stores } = await database.containers.createIfNotExists({ id: "stores", partitionKey: { paths: ["/id"] } });
  const { container: readings } = await database.containers.createIfNotExists({ id: "readings", partitionKey: { paths: ["/storeId"] } });

  for (const s of data.stores) await stores.items.upsert(s);
  console.log(`Upserted ${data.stores.length} stores`);

  for (const r of data.readings) await readings.items.upsert(r);
  console.log(`Upserted ${data.readings.length} readings`);

  // Sanity check: read one store back
  const { resource } = await stores.item(data.stores[0].id, data.stores[0].id).read();
  console.log("Read back:", resource.name, resource.latest);
}

main().catch(err => { console.error(err.message); process.exit(1); });