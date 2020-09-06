import sys
import queue

from crossword import *

class Queue:

    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)
    
    def __str__(self):
        print('Items in queue')
        for elem in self.items:
            print(elem)

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = list(word)[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()      
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for k in self.domains:
            for x in self.domains[k].copy():
                if (k.length > len(x) or k.length < len(x)):
                    self.domains[k].remove(x)
        print('Old Domain: ',self.domains)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        constraints = self.crossword.overlaps[x, y]
        if constraints is None:
            return revised
    
        v2_words = [w[constraints[1]] for w in self.domains[y]]
        for v1 in self.domains[x].copy():
            # No confussion between letters
            if v1[constraints[0]] in v2_words:
                continue
            else:
                # Confussion found(y letter not present in x)
                self.domains[x].remove(v1)
                revised = True
        
        # print('\n\nDomain after revise called: ',self.domains)
        return revised  
        raise NotImplementedError


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = Queue()
        for x in self.crossword.variables:
            for y in self.crossword.neighbors(x):
                queue.enqueue((x,y))
        while not queue.isEmpty():
            (x,y) = queue.dequeue()
            if self.revise(x,y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x) - {y}:
                        queue.enqueue((z,x))
        print('Updated Domains: ',self.domains)
        return True
        raise NotImplementedError


    def get_neighbors(self, var):
        variables = list(self.domains.keys())
        var_neighbors = set()
        for x in variables:
            if x != var and self.crossword.overlaps[(var,x)] is not None:
                var_neighbors.add(x) 
        return var_neighbors 

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for v in self.crossword.variables:
            if not self.domains[v]:
                return False
            else:
                assignment[v] = self.domains[v]
        return True
        raise NotImplementedError

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        words = []

        # Empty words found
        if not self.assignment_complete(assignment):
            return False

        # Verify all values are distinct and have proper length
        for k, v in assignment.items():
            if v not in words:
                words.append(v)
            else:
                return False
            for val in assignment[k]:
                if k.length != len(val):
                    return False
        # Check for conflicts between variables
        for x in self.crossword.variables:
            # Get each neighbor of x
            print('x is',x)
            for y in self.crossword.neighbors(x):
                #print('y is:',y)
                if self.crossword.overlaps[x,y] is not None:
                    print('Overlap:',self.crossword.overlaps[x,y])
                    a,b = self.crossword.overlaps[x,y]
                    print('a,b',a,b)
                    print('x is:',self.domains[x].values())
                    print('y is:',assignment[y])
                 
        return True
        raise NotImplementedError

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        neighbors = self.get_neighbors(var)
        print('Neighbors',neighbors)
        ans = []
        for word1 in self.domains[var]:
            cnt = 0
            for nei in neighbors:
                for word2 in self.domains[nei]:
                    (i,j) = self.crossword.overlaps[(var,nei)]
                    print('word1[i] word2[j]',word1[i],word2[j])
                    if word1[i] != word2[j]:
                        cnt += 1
            ans.append((word1,cnt))
        ans.sort(key = lambda x : x[1])
        ans = list(map(lambda x : x[0], ans))
        return ans
        raise NotImplementedError

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        vars = set(self.domains.keys()) - set(assignment.keys())
        ans = []
        for variab in vars:
            heur = len(self.domains[variab]) + len(self.get_neighbors(variab))
            ans.append((variab,heur))
        ans.sort(key=lambda x:x[1], reverse = True)
        return ans[0][0]
        raise NotImplementedError

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            print('Complete assignment')
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            new_assignment = assignment.copy()
            assignment[var] = value 
            if self.consistent(new_assignment):
                assignment[var] = value
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            del assignment[var]
        return None
        raise NotImplementedError


def main():

    # Check usage
    #if len(sys.argv) not in [3, 4]:
    #    sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    #structure = sys.argv[1]
    structure = "data/structure0.txt"

    #words = sys.argv[2]
    words = "data/words0.txt"

    #output = sys.argv[3] if len(sys.argv) == 4 else None
    output = "output.png"
    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
        #creator.print(assignment)
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
