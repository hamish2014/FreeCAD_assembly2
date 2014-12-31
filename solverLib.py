import numpy
from numpy.linalg import norm
from numpy.random import rand

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

class GradientApproximatorForwardDifference:
    def __init__(self, f):
        self.f = f
    def __call__(self, X, eps=10**-7, f0=None):
        n = len(X)
        if f0 == None:
            f0 = self.f(X)
        f0 = numpy.array(f0)
        if f0.shape == () or f0.shape == (1,):
            grad_f = numpy.zeros(n)
        else:
            grad_f = numpy.zeros([n,len(f0)])
        for i in range(n):
            X_c = X.copy()
            X_c[i] = X[i] + eps
            f_c =  self.f(X_c)
            grad_f[i] = (f_c - f0)/eps
        return grad_f.transpose()

def solve_via_Newtons_method( f, x0, maxStep, grad_f=None, x_tol=10**-6, f_tol=None, maxIt=100, randomPertubationCount=2, 
                              debugPrintLevel=0, printF=toStdOut,  lineSearchIt=10, lineSearchIt_x0=20, ):
    '''
    solve a system of non-linear equation using netwons method.
    '''
    n = len(x0)
    x = numpy.array(x0)
    x_c = numpy.zeros(n) * numpy.nan
    x_prev =  numpy.zeros( [ maxIt+1, n ] ) #used to check against cyclic behaviour, for randomPertubationCount
    x_prev[0,:] = x
    if grad_f == None:
        grad_f = GradientApproximatorForwardDifference(f)
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
        if f_tol <> None:
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
        x_c, residuals, rank, s = numpy.linalg.lstsq( A, b)
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
            x_next =  quadraticLineSearch( f_ls, x, norm(b), x_c, lineSearchIt, lineSearchIt_x0, debugPrintLevel, printF )
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

phi = (5.0**0.5 - 1)/2
def goldenSectionSearch( f, x1, f1, intialStep, it, it_min_at_x1, debugPrintLevel, printF): #f1 added to save resources...
    lam1,lam2,lam3,lam4 = 0.0, phi**2, phi, 1.0
    f2 = f( x1 + lam2*intialStep )
    f3 = f( x1 + lam3*intialStep )
    f4 = f( x1 + lam4*intialStep )
    if debugPrintLevel > 2:
        printF('    goldenSection search   lam1,lam2,lam3,lam4    %1.2e, %1.2e, %1.2e %1.2e    f1,  f2,  f3,  f4   %1.2e, %1.2e, %1.2e %1.2e' % ( lam1,lam2,lam3,lam4,f1,f2,f3,f4  ))
    for k in range(it_min_at_x1):
        min_f = min([f1,f2,f3,f4])
        if min_f == f2 or min_f == f1 :
            lam4 = lam3
            lam3 = lam2
            f4 = f3
            f3 = f2
            lam2 = lam1 + phi**2 * (lam4 - lam1)
            f2 = f( x1 + lam2*intialStep ) 
        elif min_f == f3 :
            lam1 = lam2
            lam2 = lam3
            f1 = f2
            f2 = f3
            lam3 = lam1 + phi * (lam4 - lam1)
            f3 = f( x1 + lam3*intialStep )  
        elif min_f == f4 :
            lam2 = lam3
            lam3 = lam4
            f2 = f3
            f3 = f4
            lam4 = lam1 + (phi**-1) * (lam4 - lam1)
            f4 = f( x1 + lam4*intialStep )
        if debugPrintLevel > 2:
            printF('    goldenSection search   lam1,lam2,lam3,lam4    %1.2e, %1.2e, %1.2e %1.2e    f1,  f2,  f3,  f4   %1.2e, %1.2e, %1.2e %1.2e' % ( lam1,lam2,lam3,lam4,f1,f2,f3,f4  ))
        if lam1 > 0 and k+1 >= it:
            break
    lam_min = { f1:lam1, f2:lam2, f3:lam3, f4:lam4 }[ min([f1,f2,f3,f4]) ]
    return x1 + lam_min*intialStep

def quadraticLineSearch( f, x1, f1, intialStep, it, it_min_at_x1, debugPrintLevel, printF, tol_stag=2): 
    Lam = [ 0.0, 1.0, 2.0 ]
    Y = [ f1, f(x1 + Lam[1]*intialStep) ,  f(x1 + Lam[2]*intialStep) ]
    y_min_prev = min(Y)
    count_stagnation = 0
    if debugPrintLevel > 2 :
            printF('    quadratic line search   it 0, fmin %1.2e' %   min(Y) )
    for k in range(it):
        quadraticCoefs = numpy.polyfit( Lam, Y, 2)
        if quadraticCoefs[0] == 0:
            break
        lam_c = -quadraticCoefs[1] / (2*quadraticCoefs[0]) #diff poly a*x**2 + b*x + c -> grad_poly = 2*a*x + b
        lam_c = min( max(Lam)*3, Lam)
        if lam_c < 0:
            lam_c = 1.0 / (k + 1) ** 2
        delInd = Y.index( max(Y) )
        del Lam[delInd], Y[delInd]
        Lam.append(lam_c)
        Y.append(f(x1 + lam_c*intialStep))
        if debugPrintLevel > 2:
            printF('    quadratic line search   it %i, fmin %1.2e' % ( k+1, min(Y)) )
        if min(Y) == y_min_prev:
            count_stagnation = count_stagnation + 1
            if count_stagnation > tol_stag:
                if debugPrintLevel > 2:  printF('    terminating quadratic line search as count_stagnation > tol_stag')
                break
        else:
            y_min_prev = min(Y)
            count_stagnation = 0
    lamMin = Lam[ Y.index( min(Y) ) ]
    return x1 + lamMin*intialStep


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
    for i in range(2):
        X = rand(2)*10-5
        print('    X %s' % X)
        print('    grad_f(X) analytical:   %s' % grad_f2(X))
        print('    grad_f(X) randomPoints: %s' % grad_f_rp(X))
        print('    grad_f(X) forwardDiff.: %s' % grad_f_fd(X))
        print('  norm(analytical-randomPoints) %e' % norm(grad_f2(X) - grad_f_rp(X)) )
        
    print('now of a function which returns multiple values')
    grad_f_rp = GradientApproximatorRandomPoints(f1)
    grad_f_fd = GradientApproximatorForwardDifference(f1)
    for i in range(2):
        X = rand(2)*10-5
        print('  X %s' % X)
        print('  grad_f(X) analytical:')
        prettyPrintArray(grad_f1(X), toStdOut, '    ','%1.6e')
        print('  grad_f(X) randomPoints:')
        prettyPrintArray(grad_f_rp(X), toStdOut, '    ','%1.6e')
        print('  grad_f(X) forwardDiff:')
        prettyPrintArray(grad_f_fd(X), toStdOut, '    ','%1.6e')
        print('  error %e' % norm(grad_f1(X) - grad_f_rp(X))) 

    xRoots = solve_via_Newtons_method(f2, rand(2)+3, maxStep, x_tol=0, debugPrintLevel=3, f_tol=10**-12)
