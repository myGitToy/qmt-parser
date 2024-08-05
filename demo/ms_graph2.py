from msgraph import GraphServiceClient

# Define the credentials variable
credentials = ...

graph_client = GraphServiceClient(credentials, scopes)
result = await graph_client.me.onenote.notebooks.get()