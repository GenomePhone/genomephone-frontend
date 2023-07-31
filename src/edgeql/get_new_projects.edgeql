SELECT Project {
    name,
    reference,
    targets
} 
FILTER .state = <ProjectState>"running";