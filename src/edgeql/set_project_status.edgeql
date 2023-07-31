UPDATE Project
FILTER .id = <uuid>$id
SET {
    state := <ProjectState>$state
}