        offset = ''
        scilims = plt.rcParams['axes.formatter.limits']
        if scilims[0] < scilims[1]:
            for power in (5,4,3,2,1):
                xp = scilims[1]*power
                if vymax >= 10.**xp:
                    volumeAxes.ticklabel_format(useOffset=False,scilimits=(xp,xp),axis='y')
                    offset = ' $10^{'+str(xp)+'}$'
                    break
        elif scilims[0] == scilims[1] and scilims[1] != 0:
            volumeAxes.ticklabel_format(useOffset=False,scilimits=scilims,axis='y')
            offset = ' $10^'+str(scilims[1])+'$'
