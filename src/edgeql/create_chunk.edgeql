UPDATE Genome 
FILTER .id = <uuid>$parent_id
SET {
    chunks += (INSERT Chunk {data := <bytes>$data})
}