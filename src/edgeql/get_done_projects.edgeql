SELECT Project {
    name,
    reference,
    targets: {
        chunks: {
            result
        }
    }
} 
FILTER .state = <ProjectState>"running" AND .targets.chunks.result != "";