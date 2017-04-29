import numpy
from numpy.linalg import norm
from numpy.random import rand
from lineSearches import *

def toStdOut(txt):
    print(txt)

def prettyPrintArray( A, printF, indent='  ', fmt='%1.1e' ):
    def pad(t):
        return t if t[0] == '-' else ' ' + t
    for r in A:
        txt = '  '.join( pad(fmt % v) for v in r)
        printF(indent + '[ %s ]' % txt)

def solve_via_slsqp( constraintEqs, x0, bounds=None , iterations=160, fprime=None , f_tol=10.0**-3):
    import scipy.optimize
    algName = 'scipy.optimize.fmin_slsqp (Sequential Least SQuares Programming)'
    errorNorm = lambda x: numpy.linalg.norm(constraintEqs(x))
    R = scipy.optimize.fmin_slsqp( errorNorm, x0, bounds=bounds, disp=False, full_output=True, iter=iterations, fprime=fprime, acc=f_tol**2)
    optResults = dict( zip(['xOpt', 'fOpt' , 'iter', 'imode', 'smode'], R ) ) # see scipy.optimize.fmin_bfgs docs for info
    if optResults['imode'] == 0:
        warningMsg = ''
    else:
        warningMsg = optResults['smode']
    return algName, warningMsg, optResults

class GradientApproximatorRandomPoints:
    def __init__(self, f):
        '''samples random points around a given X. as to approximate the gradient.
        Random sample should help to aviod saddle points.
        Testing showed that noise on gradient causes to scipy.optimize.fmin_slsqp to bomb-out so does not really help...
        '''
        self.f = f
    def __call__(self, X, eps=10**-7):
        n = len(X)
        samplePoints = eps*( rand(n+1,n) - 0.5 )
        #print(samplePoints)
        #samplePoints[:,n] = 1
        values = [ numpy.array(self.f( X + sp )) for  sp in samplePoints ]
        #print(values[0].shape)
        A = numpy.ones([n+1,n+1])
        A[:,:n] = samplePoints 
        x_c, residuals, rank, s = numpy.linalg.lstsq( A, values )
        return x_c[:-1].transpose()

def addEps( x, dim, eps):
    y = x.copy()
    y[dim] = y[dim] + eps
    return y

class GradientApproximatorForwardDifference:
    def __init__(self, f):
        self.f = f
    def __call__(self, x, eps=10**-7, f0=None):
        if hasattr(self.f,'addNote'): self.f.addNote('starting gradient approximation')
        n = len(x)
        if f0 == None:
            f0 = self.f(x)
        f0 = numpy.array(f0)
        if f0.shape == () or f0.shape == (1,):
            grad_f = numpy.zeros(n)
        else:
            grad_f = numpy.zeros([n,len(f0)])
        for i in range(n):
            f_c = self.f( addEps(x,i,eps) )
            grad_f[i] = (f_c - f0)/eps
        if hasattr(self.f,'addNote'): self.f.addNote('finished gradient approximation')
        return grad_f.transpose()

class GradientApproximatorCentralDifference:
    def __init__(self, f):
        self.f = f
    def __call__(self, x, eps=10**-6):
        n = len(x)
        if hasattr(self.f,'addNote'): self.f.addNote('starting gradient approximation')
        grad_f = None
        for i in range(n):
            f_a = self.f( addEps(x,i, eps) )
            f_b = self.f( addEps(x,i,-eps) )
            if grad_f == None:
                if f_a.shape == () or f_a.shape == (1,):
                    grad_f = numpy.zeros(n)
                else:
                    grad_f = numpy.zeros([n,len(f_a)])
            grad_f[i] = (f_a - f_b)/(2*eps)
        if hasattr(self.f,'addNote'): self.f.addNote('finished gradient approximation')
        return grad_f.transpose()

def solve_via_Newtons_method( f_org, x0, maxStep, grad_f=None, x_tol=10**-6, f_tol=None, maxIt=100, randomPertubationCount=2, 
                              debugPrintLevel=0, printF=toStdOut, lineSearchIt=5, record=False):
    '''
    determine the routes of a non-linear equation using netwons method.
    '''
    f = SearchAnalyticsWrapper(f_org) if record else f_org
    n = len(x0)
    x = numpy.array(x0)
    x_c = numpy.zeros(n) * numpy.nan
    x_prev =  numpy.zeros( [ maxIt+1, n ] ) #used to check against cyclic behaviour, for randomPertubationCount
    x_prev[0,:] = x
    if grad_f == None:
        #grad_f = GradientApproximatorForwardDifference(f)
        grad_f = GradientApproximatorCentralDifference(f)
    if lineSearchIt > 0:
        f_ls = lambda x: norm(f(x))
    for i in range(maxIt):
        b = numpy.array(-f(x))
        singleEq = b.shape == () or b.shape == (1,)
        if debugPrintLevel > 0:
            printF('it %02i: norm(prev. step) %1.1e norm(f(x))  %1.1e' % (i, norm(x_c), norm(-b)))
        if debugPrintLevel > 1:
            printF('  x    %s' % x)
            printF('  f(x) %s' % (-b))
        if norm(x_c) <= x_tol:
            break
        if f_tol != None:
            if singleEq and abs(b) < f_tol:
                break
            elif singleEq==False and all( abs(b) < f_tol ):
                break
        if not isinstance( grad_f, GradientApproximatorForwardDifference):
            A = grad_f(x)
        else:
            A = grad_f(x, f0=-b)
        if len(A.shape) == 1: #singleEq
            A = numpy.array([A])
            b = numpy.array([b])
        try:
            x_c, residuals, rank, s = numpy.linalg.lstsq( A, b)
        except ValueError, msg:
            printF('  solve_via_Newtons_method numpy.linalg.lstsq failed: %s.  Setting x_c = x' % str(msg)) 
            x_c = x
        if debugPrintLevel > 1:
            if singleEq:
                printF('  grad_f : %s' % A) 
            else:
                printF('  grad_f :')
                prettyPrintArray(A, printF, '    ')
            printF('  x_c    %s' % x_c)
        r = abs(x_c / maxStep)
        if r.max() > 1:
            x_c = x_c / r.max()
        if lineSearchIt > 0:
            #x_next = goldenSectionSearch( f_ls, x, norm(b), x_c, lineSearchIt, lineSearchIt_x0, debugPrintLevel, printF )
            x_next =  quadraticLineSearch( f_ls, x, norm(b), x_c, lineSearchIt, debugPrintLevel-2, printF, tol_x=x_tol )
            x_c = x_next - x
        x = x + x_c
        if randomPertubationCount > 0 : #then peturb as to avoid lock-up [i.e jam which occurs when trying to solve axis direction constraint]
            distances = ((x_prev[:i+1,:] -x)**2).sum(axis=1)
            #print(distances)
            if any(distances <= x_tol) :
                if debugPrintLevel > 0: 
                    printF(' any(distances < x_tol) therefore randomPertubation...')
                x_p = (0.5 - rand(n)) * numpy.array(maxStep)* (1 - i*1.0/maxIt)
                x = x + x_p
                x_c = x_c + x_p
                randomPertubationCount = randomPertubationCount - 1
            x_prev[i,:] = x
    return x

analytics = {}
class SearchAnalyticsWrapper:
    def __init__(self, f):
        self.f = f
        self.x = []
        self.f_x = []
        self.notes = {}
        analytics['lastSearch'] = self
    def __call__(self, x):
        self.x.append(x)
        self.f_x.append( self.f(x) )
        return self.f_x[-1]
    def addNote(self, note):
        key = len(self.x)
        assert not self.notes.has_key(key)
        self.notes[key] = note
    def __repr__(self):
        return '<SearchAnalyticsWrapper %i calls made>' % len(self.x)
    def plot(self):
        from matplotlib import pyplot
        pyplot.figure()
        it_ls = [] #ls = lineseach
        y_ls = []
        it_ga = [] #gradient approximation
        y_ga = []
        gradApprox = False
        for i in range(len(self.x)):
            y = norm( self.f_x[i] ) + 10**-9
            if self.notes.has_key(i):
                if self.notes[i] == 'starting gradient approximation':
                    gradApprox = True
                if self.notes[i] == 'finished gradient approximation':
                    gradApprox = False
            if gradApprox:
                it_ga.append( i )
                y_ga.append( y ) 
            else:
                it_ls.append( i )
                y_ls.append( y )
        pyplot.semilogy( it_ls, y_ls, 'go') 
        pyplot.semilogy( it_ga, y_ga, 'bx') 
        pyplot.xlabel('function evaluation')
        pyplot.ylabel('norm(f(x)) + 10**-9')
        pyplot.legend(['line searches', 'gradient approx' ])
                      
        pyplot.show()
        


if __name__ == '__main__':
    print('testing solver lib')

    def f1( x) :
        return numpy.array([
                x[0] + x[1] -1,
                x[0]**2 - x[1] - 5
                ])
    def grad_f1(x):
        return numpy.array([
                [1, 1],
                [2*x[0], -1]
                ])
    maxStep = [0.5, 0.5]

    xRoots = solve_via_Newtons_method(f1, rand(2)+3, maxStep, x_tol=0, debugPrintLevel=2)
    #xRoots = solve_via_Newtons_method_LS(f1, grad_f1, rand(2)+3, maxStep, debugPrintLevel=3)

    print('Testing GradientApproximatorRandomPoints')
    print('now on f2, which returns a single real value')
    def f2(X) :
        y,z=X
        return y + y*z + (1.0-y)**3
    def grad_f2(X):
        y,z=X
        return  numpy.array([ 1 + z - 3*(1.0-y)**2, y ])
    print('first on f2, which return a single real value')
    grad_f_rp = GradientApproximatorRandomPoints(f2)
    grad_f_fd = GradientApproximatorForwardDifference(f2)
    grad_f_cd = GradientApproximatorCentralDifference(f2)
    for i in range(2):
        X = rand(2)*10-5
        print('    X %s' % X)
        print('    grad_f(X) analytical:   %s' % grad_f2(X))
        print('    grad_f(X) randomPoints: %s' % grad_f_rp(X))
        print('    grad_f(X) forwardDiff.: %s' % grad_f_fd(X))
        print('    grad_f(X) centralDiff.: %s' % grad_f_cd(X))
        print('  norm(analytical-randomPoints) %e' % norm(grad_f2(X) - grad_f_rp(X)) )
        
    print('now of a function which returns multiple values')
    grad_f_rp = GradientApproximatorRandomPoints(f1)
    grad_f_fd = GradientApproximatorForwardDifference(f1)
    grad_f_cd = GradientApproximatorCentralDifference(f1)
    for i in range(2):
        X = rand(2)*10-5
        print('  X %s' % X)
        print('  grad_f(X) analytical:')
        prettyPrintArray(grad_f1(X), toStdOut, '    ','%1.6e')
        print('  grad_f(X) randomPoints:')
        prettyPrintArray(grad_f_rp(X), toStdOut, '    ','%1.6e')
        print('  grad_f(X) forwardDiff:')
        prettyPrintArray(grad_f_fd(X), toStdOut, '    ','%1.6e')
        print('  grad_f(X) centralDiff:')
        prettyPrintArray(grad_f_cd(X), toStdOut, '    ','%1.6e')


        print('  error rp %e' % norm(grad_f1(X) - grad_f_rp(X))) 

    xRoots = solve_via_Newtons_method(f2, rand(2)+3, maxStep, x_tol=0, debugPrintLevel=3, f_tol=10**-12)

    print(analytics['lastSearch'])
    analytics['lastSearch'].plot()
