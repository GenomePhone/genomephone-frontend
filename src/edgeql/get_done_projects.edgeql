SELECT Project {
    name,
    ref,
    targets: {
        chunks: {
            result
        }
    }
} 
FILTER .state = <ProjectState>"running" AND .targets.chunks.result != "";