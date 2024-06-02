import networkx as nx 
import pulp as pl

# Define graph creation
def createGraph(n):
    GS = nx.DiGraph()
    for i in range (n):
        GS.add_node(i, r=2)
    for i in range (n-1):
        GS.add_edge(i, i+1, r=5)
    return GS

# Create target graph N
N = nx.DiGraph()
for i in range (5):
    N.add_node(i, a=10)
for i in range (4):
    N.add_edge(i, i+1, a = 10)
    N.add_edge(i+1, i, a = 10)
    
# Create subgraph
GS_1 = createGraph(3)
GS_2 = createGraph(4)
GS_3 = createGraph(2)

GS = [GS_1, GS_2, GS_3]

# ILP Problem
problem = pl.LpProblem(name='Graph-Mapping', sense = pl.LpMaximize)

#Decision variables for nodes and edges
xNode = pl.LpVariable.dicts("xNode",
                      ((s, n, i)
                      for s, subgraph in enumerate(GS)
                      for n in subgraph.nodes
                      for i in N.nodes),
                      cat = pl.LpBinary
)

xEdge = pl.LpVariable.dicts("xEdge", 
                            ((s, w, v, i, j) 
                             for s, subgraph in enumerate(GS) 
                             for w, v in subgraph.edges 
                             for i, j in N.edges),
                            cat=pl.LpBinary)

pi = pl.LpVariable.dicts("pi", (s for s in range(len(GS))), cat = pl.LpBinary)
phi = pl.LpVariable.dicts("phi", 
                          ((s, k) 
                           for s in range(len(GS)) 
                           for k in N.nodes),
                          cat=pl.LpBinary)
z = pl.LpVariable.dicts("z", 
                        ((s, k) 
                         for s in range(len(GS)) 
                         for k in N.nodes),
                        cat=pl.LpBinary)

# Attribute of the target graph
aNode = nx.get_node_attributes(N, "a")
aEdge = nx.get_edge_attributes(N, "a")

# Constraints
for s, subgraph in enumerate(GS):
    rNode = nx.get_node_attributes(subgraph,"r")
    rEdge = nx.get_edge_attributes(subgraph,"r")
    
    # C1 constraint
    for i in N.nodes:
        problem += (
            pl.lpSum(
                xNode[(s, n, i)] * rNode[n]
                for n in subgraph.nodes
            ) <= aNode[i] * pl.lpSum(phi[(s, k)] for k in N.nodes),
            f'C1_{s}_{i}'
        )

    
    #C2 constraint
    for i, j in N.edges:
        problem += (
            pl.lpSum(
                xEdge[(s, w, v, i, j)] * rEdge[(w, v)]
                for w, v in subgraph.edges
            ) <= aEdge[(i, j)] * pl.lpSum(phi[(s, k)] for k in N.nodes),
            f'C2_{s}_{i}_{j}'
        )
        
    #C3 constraint
    for i in N.nodes:
        for k in N.nodes:
            problem += (
                pl.lpSum(
                    xNode[(s, n, i)]
                    for n in subgraph.nodes
                ) <= z[(s, k)],
                f'C3_{s}_{i}_{k}'
        )
    
    #C4 constraint
    for n in subgraph.nodes:
        for k in N.nodes:
            problem += (    
                pl.lpSum(
                    xNode[(s, n, i)]
                    for i in N.nodes
                ) == z[(s, k)],
                f'C4_{s}_{n}_{k}'
            )
    # C5 constraints
    big_M = 100  # Define a sufficiently large value for M
    for (w, v) in subgraph.edges:
        for k in N.nodes:
            for i in N.nodes:
                for j in N.nodes:
                    if i != j:
                        if (s, w, v, i, j) in xEdge and (s, w, v, j, i) in xEdge:
                            problem += (
                                xEdge[(s, w, v, i, j)] - xEdge[(s, w, v, j, i)] 
                                - (xNode[(s, v, i)] - xNode[(s, w, i)]) <= big_M * (1 - phi[(s, k)]),
                                f'C5_{s}_{w}_{v}_{i}_{j}_{k}_1'
                            )
                            problem += (
                                xEdge[(s, w, v, i, j)] - xEdge[(s, w, v, j, i)] 
                                - (xNode[(s, v, i)] - xNode[(s, w, i)]) >= -big_M * (1 - phi[(s, k)]),
                                f'C5_{s}_{w}_{v}_{i}_{j}_{k}_2'
                            )
    #C6 constraint
for s in range(len(GS)):
    problem += (
        pl.lpSum(phi[(s, k)] for k in N.nodes) == pi[s],
        f'C6_{s}'
    )
    
    #C7 constraint
for s in range(len(GS)):
    for k in N.nodes:
        problem += (
            z[(s, k)] <= pi[s],
            f'C7_{s}_{k}_1'
            )
        problem += (
            z[(s, k)] <= phi[(s, k)],
            f'C7_{s}_{k}_2'
        ) 
        problem += (
            z[(s, k)] <= pi[s] - phi[(s, k)] - 1,
            f'C7_{s}_{k}_3'
        )
        
# Objective function
problem += pl.lpSum(pi[s] for s in range(len(GS)))

print(problem)

# Solve the problem
result = problem.solve()
print(pl.LpStatus[result])

# Output
for v in problem.variables():
    print(v.name, "=", v.varValue)
    