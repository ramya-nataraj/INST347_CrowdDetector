// main.bicep - Holiday Shopping Crowd Detector Infrastructure
param location string = 'mexicocentral'

// 1. Serverless Object Storage Account (Fixed: 'st' + unique string = ~15 characters, well under the 24-char limit)
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: 'stcrowddetector'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
  }
}

// 2. Cosmos DB Account in Serverless Mode (For store metadata and user alerts)
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'cosmosdb-crowddetector'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}
