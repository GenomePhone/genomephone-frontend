SELECT Project {
    name,
    ref,
    targets
} 
FILTER .state = <ProjectState>"running";