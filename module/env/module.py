#
# Collective Knowledge (environment)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# set environment for tools and libraries 
# (multiple versions of the same tools/libraries can co-exist)

def set(i):
    """
    Input:  {
              (host_os)              - host OS (detect, if ommitted)
              (target_os)            - target OS (detect, if ommitted)
              (target_device_id)     - target device ID (detect, if omitted)

              (repo_uoa)             - repo where to limit search

              (uoa)                  - environment UOA entry
               or
              (tags)                 - search UOA by tags (separated by comma)

              (local)                - if 'yes', add host_os, target_os, target_device_id to search

              (key)                  - key from deps (to set env with path)
              (name)                 - user-friendly name of the dependency (if needs to be resolved)

              (deps)                 - already resolved deps
              (skip_auto_resolution) - if 'yes', do not check if deps are already resolved
              (skip_default)         - if 'yes', skip detection of default installed software version

              (bat_file)             - if !='', use this filename to generate/append bat file ...
              (bat_new)              - if 'yes', start new bat file

              (env)                  - existing environment

              (print)                - if 'yes', print found environment

              (random)               - if 'yes' and there is a choice, select random
                                       (useful for quiet experiment crowdsourcing such as sw/hw crowdtuning)

              (quiet)                - if 'yes', automatically provide default answer to all questions when resolving dependencies ... 
            }

    Output: {
              return           - return code =  0, if successful
                                             = 32, if environment was deleted (env_uoa - env which was not found)
                                             >  0, if error
              (error)          - error text if return > 0

              env_uoa          - found environment UOA
              env              - updated environment
              bat              - string for bat file
              lst              - all found entries
              dict             - meta of the selected env entry
              detected_version - detected version of a software
            }

    """

    import os
    import copy
    import json

    o=i.get('out','')
    oo=''
    if o=='con': oo='con'

    ran=i.get('random','')
    quiet=i.get('quiet','')

    name=i.get('name','')

    # Clean output file
    sar=i.get('skip_auto_resolution','')
    cdeps=i.get('deps',{})

    sd=i.get('skip_default','')

    bf=i.get('bat_file','')
    if bf!='' and os.path.isfile(bf): os.remove(bf)

    # Check host/target OS/CPU
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    tdid=i.get('target_device_id','')
    if tdid=='': tdid=i.get('device_id','')

    user_env=False
    if hos!='' or tos!='' or tdid!='': user_env=True

    # Get some info about OS
    ii={'action':'detect',
        'module_uoa':cfg['module_deps']['platform.os'],
        'host_os':hos,
        'target_os':tos,
        'device_id':tdid,
        'skip_info_collection':'yes'}
    r=ck.access(ii)
    if r['return']>0: return r

    hos=r['host_os_uid']
    hosx=r['host_os_uoa']
    hosd=r['host_os_dict']

    ck_os_name=hosd['ck_name']

    tos=r['os_uid']
    tosx=r['os_uoa']
    tosd=r['os_dict']

    # Check if base is different
    x1=hosd.get('base_uid','')
    x2=hosd.get('base_uoa','')
    if x1!='' and x2!='': 
       hos=x1
       hosx=x2
    x1=tosd.get('base_uid','')
    x2=tosd.get('base_uoa','')
    if x1!='' and x2!='': 
       tos=x1
       tosx=x2

    remote=tosd.get('remote','')

    tbits=tosd.get('bits','')

    hplat=hosd.get('ck_name','')

    eset=hosd.get('env_set','')
    svarb=hosd.get('env_var_start','')
    svare=hosd.get('env_var_stop','')
    sdirs=hosd.get('dir_sep','')
    evs=hosd.get('env_var_separator','')
    eifs=hosd.get('env_quotes_if_space','')
    nout=hosd.get('no_output','')

    # Check environment UOA
    enruoa=i.get('repo_uoa','')
    tags=i.get('tags','')
    duoa=i.get('uoa','')

    lx=0
    dd={}
    setup={}

    # Search
    ii={'action':'search',
        'module_uoa':work['self_module_uid'],
        'tags':tags,
        'repo_uoa':enruoa,
        'data_uoa':duoa,
        'add_info':'yes',
        'add_meta':'yes'} # Need to sort by version, if ambiguity

    if user_env or i.get('local','')=='yes':
       setup={'host_os_uoa':hos,
              'target_os_uoa':tos,
              'target_os_bits':tbits}
       ii['search_dict']={'setup':setup}

    iii=copy.deepcopy(ii) # may need to repeat after registration

    # Prepare possible warning
    x='required software'
    if name!='': x='"'+name+'"'
    war='no registered CK environment was found for '+x+' dependency with tags="'+tags+'"'
    if len(setup)>0:
       ro=readable_os({'setup':setup})
       if ro['return']>0: return ro
       setup1=ro['setup1']

       war+=' and setup='+json.dumps(setup1)

    # Search for environment entries
    r=ck.access(ii)
    if r['return']>0: return r
    l=r['lst']
    lx=len(l)

    auoas=[]

    if lx==0 and duoa!='':
       return {'return':33, 'error':'either missing env ('+duoa+') or it exists but something changes in its dependencies or setup ('+str(setup)+'):'}

    # If no entries, try to detect default ones and repeat
    history_deps=[]
    showed_warning=False
    if lx==0:
       if o=='con' and tags!='':
          ck.out('')
          ck.out(' ********')
          ck.out(' WARNING: '+war)
          ck.out('')

          showed_warning=True

       # First, try to detect already installed software, but not registered (default)
       if sd!='yes':
          if o=='con':
             ck.out('  Trying to automatically detect required software ...')

          ii={'action':'search',
              'module_uoa':cfg['module_deps']['soft'],
              'tags':tags,
              'add_meta':'yes'}
          rx=ck.access(ii)
          if rx['return']>0: return rx

          slst=rx['lst']

          # Sorting and checking which has detection module
          detected=''
          ssi=0
          found=False
          for q in sorted(slst, key=lambda v: v.get('meta',{}).get('sort',0)):
              met=q.get('meta',{})
              auoa=q['data_uoa']
              auid=q['data_uid']
              aname=met.get('soft_name','')

              auoas.append(q['data_uoa'])
              ds=met.get('auto_detect','')
              if ds=='yes':
                 if auid not in history_deps:
                    # Check target
                    rx=ck.access({'action':'check_target',
                                  'module_uoa':cfg['module_deps']['soft'],
                                  'dict':met.get('customize',{}),
                                  'host_os_uoa':hosx,
                                  'host_os_dict':hosd,
                                  'target_os_uoa':tosx,
                                  'target_os_dict':tosd})
                    if rx['return']>0:
                       continue

                    history_deps.append(auid)
                    ssi+=1

                    if o=='con':
                       ck.out('')
                       ck.out('  '+str(ssi)+') Checking if "'+aname+'" ('+auoa+' / '+auid+') is installed ...')

                    # Detect software
                    ii={'action':'check',
                        'module_uoa':cfg['module_deps']['soft'],
                        'data_uoa':auid,
                        'skip_help':'yes',
                        'host_os':hos,
                        'target_os':tos,
                        'target_device_id':tdid,
#                        'deps':cdeps,
                        'out':oo}
                    if len(setup)>0:
                       ii.update(setup)
                    ry=ck.access(ii)
                    if ry['return']>0:
                       if o=='con':
                          ck.out('  (warning during intermediate step: '+ry['error']+')')
                    else:
                       found=True

                       hdeps=ry.get('deps',{})
                       for hd in hdeps:
                           xhd=hdeps[hd]
                           xxhd=xhd.get('dict',{}).get('soft_uoa','')
                           if xxhd not in history_deps:
                              history_deps.append(xxhd)

          # repeat search if at least one above setup was performed
          if not found:
             if o=='con':
                ck.out('    No software auto-detection scripts found for this software in CK :( ...')

                if len(auoas)>0:
                   ck.out('')
                   ck.out('       Checked following related CK soft entries:')
                   for q in auoas:
                       ck.out('        * '+q)

          else:
             r=ck.access(iii)
             if r['return']>0: return r
             l=r['lst']
             lx=len(l)

    # Re-check existing environment
    if lx>0:
       ilx=0
       if lx>1 and sar!='yes':
          # Try auto-resolve or prune choices
          nls=[]
          for z in range(0, lx):
              j=l[z]
              zm=j.get('meta',{})
              cus=zm.get('customize','')
              zdeps=zm.get('deps',{})

              skip=False
              for q in zdeps:
                  jj=zdeps[q]
                  juoa=jj.get('uoa','')

                  for a in cdeps:
                      if a==q:
                         aa=cdeps[a]
                         auoa=aa.get('uoa','')

                         # Tricky part ...
                         if auoa!=juoa:
                            skip=True
                            break

                  if skip: break
              if not skip: nls.append(j)

          l=nls
          lx=len(l)

       # Select sub-deps (sort by version)
       if lx>1:
          ls=sorted(l, key=lambda k: (k.get('info',{}).get('data_name',k['data_uoa']),
                                      internal_get_val(k.get('meta',{}).get('setup',{}).get('version_split',[]), 0, 0),
                                      internal_get_val(k.get('meta',{}).get('setup',{}).get('version_split',[]), 1, 0),
                                      internal_get_val(k.get('meta',{}).get('setup',{}).get('version_split',[]), 2, 0),
                                      internal_get_val(k.get('meta',{}).get('setup',{}).get('version_split',[]), 3, 0),
                                      internal_get_val(k.get('meta',{}).get('setup',{}).get('version_split',[]), 4, 0)),
                    reverse=True)

          l=ls

          if ran=='yes':
             from random import randint
             ilx=randint(0, lx-1)
          elif quiet=='yes':
             ilx=0
          else:
             if o=='con':
                xq='required software'
                if name!='': xq='"'+name+'"'

                xq+=' with tags="'+tags+'"'

                if len(setup)>0:
                   import json

                   ro=readable_os({'setup':setup})
                   if ro['return']>0: return ro
                   setup1=ro['setup1']

                   xq+=' and setup='+json.dumps(setup1)

                ck.out('')
                ck.out('More than one environment found for '+xq+':')
                zz={}
                for z in range(0, lx):
                    j=l[z]

                    zi=j.get('info',{})
                    zm=j.get('meta',{})
                    zu=j.get('data_uid','')
                    zdn=zi.get('data_name','')
                    cus=zm.get('customize','')
                    zdeps=zm.get('deps',{})
                    xsetup=zm.get('setup',{})
                    xtags=zm.get('tags','')
                    ver=cus.get('version','')

                    xtarget_os_uoa=xsetup.get('target_os_uoa','')

                    xstags=''
                    for t in xtags:
                        if t!='':
                           if xstags!='': xstags+=','
                           xstags+=t

                    zs=str(z)
                    zz[zs]=zu

                    ck.out('')
                    ck.out(zs+') '+zdn+' - v'+ver+' ('+xstags+' ('+zu+'))')

                    if len(zdeps)>0:
                       for j in sorted(zdeps, key=lambda v: zdeps[v].get('sort',0)):
                           jj=zdeps[j]
                           juoa=jj.get('uoa','')
                           jtags=jj.get('tags','')
                           jver=jj.get('ver','')

                           js='                                  '
                           js+='Dependency '+j+' (UOA='+juoa+', tags="'+jtags+'", version='+jver+')'
                           ck.out(js)

                ck.out('')
                rx=ck.inp({'text':'Select one of the options for '+xq+' or press Enter for 0: '})
                x=rx['string'].strip()

                if x=='': x='0'

                if x not in zz:
                   return {'return':1, 'error':'option is not recognized'}

                ilx=int(x)

       if ilx<len(l):
          duid=l[ilx].get('data_uid')
          duoa=duid

          dd=l[ilx].get('meta',{})

          if o=='con' and i.get('print','')=='yes':
             x=duoa
             if duid!=duoa: x+=' ('+duid+')'
             ck.out('CK environment found using tags "'+tags+'" : '+x)

    # No registered environments found and environment UOA is not explicitly defined
    if duoa=='':
#       if o=='con' and tags!='':
       if tags!='':

          if not showed_warning:
             ck.out('==========================================================================================')
             ck.out('WARNING: '+war)

          # Next, try to install via package for a given software
          ck.out('')
          ck.out('  Searching and installing CK software packages with these tags (if exist) ...')

#          if quiet=='yes':
#             ck.out('  Searching and installing package with these tags automatically ...')
#             a='y'
#          else:
#             rx=ck.inp({'text':'  Would you like to search and install package with these tags automatically (Y/n)? '})
#             a=rx['string'].strip().lower()
#
#          if a!='n' and a!='no':
          save_cur_dir=os.getcwd()

          vv={'action':'install',
              'module_uoa':cfg['module_deps']['package'],
              'out':oo,
              'tags':tags}
          vv['host_os']=hos
          vv['target_os']=tos
          vv['target_device_id']=tdid

          # Check if there is a compiler in resolved deps to reuse it
          xdeps={}
#             if len(cdeps.get('compiler',{}))>0: xdeps['compiler']=cdeps['compiler']
          if cdeps.get('compiler',{}).get('uoa','')!='': xdeps['compiler']=cdeps['compiler']
#             if len(cdeps.get('compiler-mcl',{}))>0: xdeps['compiler-mcl']=cdeps['compiler-mcl']
          if cdeps.get('compiler-mcl',{}).get('uoa','')!='': xdeps['compiler-mcl']=cdeps['compiler-mcl']
          if len(xdeps)>0: vv['deps']=xdeps

          rx=ck.access(vv)
          if rx['return']==0:
             duoa=rx['env_data_uoa']
             duid=rx['env_data_uid']

             os.chdir(save_cur_dir)
          elif rx['return']!=16:
             return rx

       if duoa=='':
          if o=='con':
             ck.out('    CK packages are not found for this software :( !')
             ck.out('')

             if len(auoas)>0:
                if len(auoas)==1:
                   rx=ck.access({'action':'print_help',
                                 'module_uoa':cfg['module_deps']['soft'],
                                 'data_uoa':auoas[0],
                                 'platform':hplat})

                   rx=ck.inp({'text':'       Would you like to manually register software, i.e. if it is in an unusual path (y/N): '})
                   x=rx['string'].strip().lower()
                   if x=='yes' or x=='yes':
                      ck.out('')
                      rx=ck.access({'action':'setup',
                                    'module_uoa':cfg['module_deps']['soft'],
                                    'data_uoa':auoas[0],
                                    'out':'con'})
                      if rx['return']>0: return rx
                      ck.out('')

                else:
                   # Show possible Wiki page
                   rx=ck.inp({'text':'       Would you like to open wiki pages about related software (with possible installation info) (y/N): '})
                   x=rx['string'].strip().lower()

                   if x=='yes' or x=='yes':
                      ck.out('')
                      for q in auoas:
                          rx=ck.access({'action':'wiki',
                                        'module_uoa':cfg['module_deps']['soft'],
                                        'data_uoa':q})
                          if rx['return']>0: return rx
                      ck.out('')


          if o=='con':
             ck.out('')
          return {'return':1, 'error':war}

    # Load selected environment entry
    r=ck.access({'action':'load',
                 'module_uoa':work['self_module_uid'],
                 'data_uoa':duoa})
    if r['return']>0: 
       if r['return']==16:
          r['return']=32
          r['env_uoa']=duoa
       return r
    d=r['dict']
    p=r['path']

    suoa=d.get('soft_uoa','')
    cs=None
    if suoa!='':
       r=ck.access({'action':'load',
                    'module_uoa':cfg['module_deps']['soft'],
                    'data_uoa':suoa})
       if r['return']>0: return r

       salias=r['data_alias']
       d['soft_alias']=salias

       # Check if has custom script
       rx=ck.load_module_from_path({'path':r['path'], 'module_code_name':cfg['custom_script_name'], 'skip_init':'yes'})
       if rx['return']==0: 
          cs=rx['code']

    # Check that all sub dependencies still exists (if full path)
    outdated=False
    to_delete=False
    err=''

    edeps=d.get('deps',{}) # dependencies of environment (normally resolved, but may change if software changes)
    for q in edeps:
        qq=edeps[q]
        cqq=qq.get('dict',{}).get('customize',{})
        sfc=cqq.get('skip_file_check','')
        fp=cqq.get('full_path','')

        if sfc!='yes' and fp!='' and not os.path.isfile(fp):
           outdated=True
           err='one of sub-dependencies ('+q+') have changed (file '+fp+' not found)'
           break

        deuoa=qq.get('uoa','')
        if deuoa!='':
           rx=ck.access({'action':'find',
                         'module_uoa':work['self_module_uid'],
                         'data_uoa':deuoa})
           if rx['return']>0:
              if rx['return']!=16: return rx
              outdated=True
              err='one of sub-dependencies ('+q+') have changed (CK environment '+deuoa+' not found)'
              break

    # Check if file exists for current dependency
    verx=''
    cus=d.get('customize',{})
    fp=cus.get('full_path','')

    tc='it appears that your environment has changed - '
    if not outdated and fp!='' and cus.get('skip_file_check','')!='yes' and not os.path.isfile(fp):
       err=tc+'software file not found in a specified path ('+fp+')'
       outdated=True

    ver_in_env=cus.get('version','') # detected version during installation
    if not outdated and ver_in_env!='':
       scmd=cus.get('soft_version_cmd',{}).get(ck_os_name,'')
       if scmd!='' and 'parse_version' in dir(cs):
          # Check version (via customized script) ...
          ii={'action':'get_version',
              'module_uoa':cfg['module_deps']['soft'],
              'full_path':fp,
              'bat':'',
              'host_os_dict':hosd,
              'target_os_dict':tosd,
              'cmd':scmd,
              'custom_script_obj':cs}
          rx=ck.access(ii)
          if rx['return']==0:
             verx=rx['version']
             if verx!='' and verx!=ver_in_env:
                err=tc+'version during installation ('+ver_in_env+') is not the same as current version ('+verx+')'
                outdated=True

    if outdated:
       if o=='con':
          ck.out('')
          ck.out('WARNING: '+err)

          ck.out('')
          rx=ck.inp({'text':'Would you like to remove outdated environment entry from CK (Y/n)? '})
          x=rx['string'].strip()

          if x=='n' or x=='no':
             return {'return':1, 'error':err}
          to_delete=True

       # Deleting outdated environment
       if to_delete:
          if o=='con':
             ck.out('')
             ck.out('Removing outdated environment entry '+duoa+' ...')

          rx=ck.access({'action':'delete',
                        'module_uoa':work['self_module_uid'],
                        'data_uoa':duoa})
          if rx['return']>0: return rx

          return {'return':1, 'error':'Outdated environment was removed - please, try again!'}

    # Prepare environment and bat
    env=i.get('env',{})
    xenv=d.get('env',{})
    env.update(xenv)

    env_call=hosd.get('env_call','')
    bin_prefix=hosd.get('bin_prefix','')

    # Process CMD first:
    sb=''

    es=d.get('env_script','')
    if es!='':
       pp=os.path.join(p,es)
       if i.get('key','')!='':
          sb+=eset+' CK_ENV_SCRIPT_'+i['key'].upper()+'='+pp+'\n'
       sb+=env_call+' '+pp+'\n'

    # Check bat file
    if bf!='':
       bn=i.get('bat_new','')
       x='a'
       if bn=='yes': x='w'

       try:
          fbf=open(bf, x)
          fbf.write(sb)
       except Exception as e: 
          fbf.close()
          return {'return':1, 'error':'problem writing environment file ('+format(e)+')'}

       fbf.close()

    return {'return':0, 'env_uoa':duoa, 'env':env, 'bat':sb, 'lst':l, 'dict':d, 'detected_version':verx}

##############################################################################
# show all installed environment

def show(i):
    """
    Input:  {
              (repo_uoa)          - repository UOA (with wildcards)
              (module_uoa)        - module UOA (with wildcards)
              (data_uoa)          - data UOA (with wildcards)

              (tags)              - prune by tags
              (target_os)         - prune by target OS
              (target_bits)       - prune by target bits
              (version)           - prune by version
              (name)              - prune by name with wildcards
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              lst          - list from search function
              view         - sorted view list
            }

    """

    o=i.get('out','')

    ruoa=i.get('repo_uoa','')
    muoa=i.get('module_uoa','')
    duoa=i.get('data_uoa','')

    tags=i.get('tags','')

    tos_uoa=i.get('target_os','')
    if tos_uoa!='':
       # Load OS
       ry=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['os'],
                     'data_uoa':tos_uoa})
       if ry['return']>0: return ry

       tos_uoa=ry['data_uoa']
       tosz=ry['dict'].get('base_uoa','')
       if tosz!='': tos_uoa=tosz

       if tags!='': tags+=','
       tags+='target-os-'+tos_uoa

    tb=i.get('target_bits','')
    if tb!='':
       if tags!='': tags+=','
       tags+=tb+'bits'

    ver=i.get('version','')
    if ver!='':
       if tags!='': tags+=','
       tags+='v'+ver

    name=i.get('name','')
    wname=False
    if name.find('*')>=0 or name.find('?')>=0:
       import fnmatch
       wname=True 
       name=name.lower()

    ii={'action':'search',
        'module_uoa':muoa,
        'repo_uoa':ruoa,
        'data_uoa':duoa,
        'tags':tags,
        'add_info':'yes',
        'add_meta':'yes'}
    rx=ck.access(ii)
    if rx['return']>0: return rx

    lst=rx['lst']

    # prepare view
    view=[]

    lv={} # length of each field

    target_os_name={} # Caching target OS names

    for q in lst:
        vv={}

        duoa=q['data_uoa']
        duid=q['data_uid']

        ruoa=q['repo_uoa']
        ruid=q['repo_uid']

        info=q['info']
        meta=q['meta']

        cus=meta.get('customize',{})
        setup=meta.get('setup','')
        tags=meta.get('tags',[])

        host_os_uoa=setup.get('host_os_uoa','')
        target_os_uoa=setup.get('target_os_uoa','')
        tbits=setup.get('target_os_bits','')
        version=setup.get('version','')
        sversion=setup.get('version_split',[])

        dname=info.get('data_name','')

        add=True
        if name!='':
           if wname:
              if not fnmatch.fnmatch(dname.lower(), name):
                 add=False
           else:
              if name!=dname:
                 add=False

        if add:
           # Check target OS
           if target_os_uoa in target_os_name:
              tduoa=target_os_name[target_os_uoa]
           else:
              # Load
              ry=ck.access({'action':'load',
                            'module_uoa':cfg['module_deps']['os'],
                            'data_uoa':target_os_uoa})
              if ry['return']>0: return ry
              tduoa=ry['data_uoa']
              target_os_name[target_os_uoa]=tduoa

           stags=''
           for t in tags:
               if t!='':
                  if stags!='': stags+=','
                  stags+=t

           vv['data_uid']=duid
           vv['repo_uid']=ruid
           vv['tags']=stags
           vv['host_os_uoa']=host_os_uoa
           vv['target_os_uoa']=tduoa
           vv['tbits']=tbits
           vv['version']=version
           vv['version_split']=sversion
           vv['data_name']=dname

           # Check length
           for k in vv:
               v=str(vv[k])
               l=len(v)
               if k not in lv: lv[k]=l
               elif l>lv[k]: lv[k]=l

           view.append(vv)

           if lv['data_name']<5: lv['data_name']=5
           if lv['target_os_uoa']<10: lv['target_os_uoa']=10
           if lv['version']<8: lv['version']=8

    # Sort by target_os_uoa, name and split version
    vs=sorted(view, key=lambda k: (k['target_os_uoa'],
                                   k['tbits'],
                                   k['data_name'],
                                   internal_get_val(k.get('version_split',[]), 0, 0),
                                   internal_get_val(k.get('version_split',[]), 1, 0),
                                   internal_get_val(k.get('version_split',[]), 2, 0),
                                   internal_get_val(k.get('version_split',[]), 3, 0),
                                   internal_get_val(k.get('version_split',[]), 4, 0)),
              reverse=True)

    # Print
    if o=='con':
       if len(vs)>0:
          # Headers
          sh ='Env UID:' + (' ' * (lv['data_uid']- 8))
          sh+=' Target OS:' + (' ' * (lv['target_os_uoa']-10))
          sh+=' Bits:'
          sh+=' Name:' + (' ' * (lv['data_name']- 5))
          sh+=' Version:' + (' ' * (lv['version']- 8))
          sh+=' Tags:'

          ck.out(sh)

          ck.out('')
          for q in vs:
              x=q['data_uid']
              sh=(' ' * (lv['data_uid']- len(x))) + x

              x=q['target_os_uoa']
              sh+=' '+(' ' * (lv['target_os_uoa']- len(x))) + x

              x=q['tbits']
              sh+=' '+(' ' * (5 - len(x))) + x

              x=q['data_name']
              sh+=' '+ x + (' ' * (lv['data_name']- len(x)))

              x=q['version']
              sh+=' '+ x + (' ' * (lv['version'] - len(x)))

              x=q['tags']
              sh+=' '+x

              ck.out(sh)

    return {'return':0, 'lst':lst, 'view':vs}

##############################################################################
# resolve all dependencies

def resolve(i):
    """
    Input:  {
              (host_os)              - host OS (detect, if ommitted)
              (target_os)            - target OS (detect, if ommitted)
              (target_device_id)     - target device ID (detect, if omitted)
                  or
              (device_id)

              (repo_uoa)             - repo where to limit search

              deps                   - dependencies dict

              (env)                  - env

              (add_customize)        - if 'yes', add to deps customize field from the environment 
                                       (useful for program compilation)

              (skip_dict)            - if 'yes', do not add to deps dict field from the environment 
                                       (useful for program compilation)

              (skip_auto_resolution) - if 'yes', do not check if deps are already resolved

              (random)               - if 'yes' and there is a choice, select random
                                       (useful for quiet experiment crowdsourcing such as sw/hw crowdtuning)

              (quiet)                - if 'yes', automatically provide default answer to all questions when resolving dependencies ... 
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              bat          - string for bat file calling all bats ...
              cut_bat      - string for bat file calling all bats (does not include deps that are explicitly excluded) ...
              deps         - updated deps (with uoa)
              env          - updated env
            }

    """

    o=i.get('out','')

    if o=='con':
       ck.out('')
       ck.out('Resolving software dependencies ...')

    sb=''
    sb1=''

    sar=i.get('skip_auto_resolution','')

    deps=i.get('deps',{})

    ran=i.get('random','')
    quiet=i.get('quiet','')

    # Check host/target OS/CPU
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    tdid=i.get('target_device_id','')
    if tdid=='': tdid=i.get('device_id','')

    user_env=False
    if hos!='' or tos!='' or tdid!='': user_env=True

    # Get some info about OS
    ii={'action':'detect',
        'module_uoa':cfg['module_deps']['platform.os'],
        'host_os':hos,
        'target_os':tos,
        'device_id':tdid,
        'skip_info_collection':'yes'}
    r=ck.access(ii)
    if r['return']>0: return r

    hos=r['host_os_uid']
    hosx=r['host_os_uoa']
    hosd=r['host_os_dict']

    tos=r['os_uid']
    tosx=r['os_uoa']
    tosd=r['os_dict']

    # Check if base is different
    x1=hosd.get('base_uid','')
    x2=hosd.get('base_uoa','')
    if x1!='' and x2!='': 
       hos=x1
       hosx=x2
    x1=tosd.get('base_uid','')
    x2=tosd.get('base_uoa','')
    if x1!='' and x2!='': 
       tos=x1
       tosx=x2

    remote=tosd.get('remote','')

    tbits=tosd.get('bits','')

    # Checking deps
    env=i.get('env',{})

    enruoa=i.get('repo_uoa','')

    ac=i.get('add_customize','')
    sd=i.get('skip_dict','')

    res=[]
    iv=0
    for k in sorted(deps, key=lambda v: deps[v].get('sort',0)):
        q=deps[k]

        ytos=tos
        ytdid=tdid
        ytosx=tosx
        ytosd=tosd

        if q.get('force_target_as_host','')=='yes':
            ytos=hos
            ytdid=''
            ytosx=hosx
            ytosd=hosd

        tags=q.get('tags','')
        name=q.get('name','')
        local=q.get('local','')
        sd=q.get('skip_deafult','')

        ek=q.get('env_key','')

        uoa=q.get('uoa','')

        # Check if restricts dependency to a given host or target OS
        rx=ck.access({'action':'check_target',
                      'module_uoa':cfg['module_deps']['soft'],
                      'dict':q,
                      'host_os_uoa':hosx,
                      'host_os_dict':hosd,
                      'target_os_uoa':ytosx,
                      'target_os_dict':ytosd})
        if rx['return']>0:
           continue

        # Try to set environment
        iv+=1

        if o=='con':
           x='*** Dependency '+str(iv)+' = '+k
           if name!='': x+=' ('+name+')'
           x+=':'
           ck.out('')
           ck.out(x)

        ii={'host_os':hos,
            'target_os':ytos,
            'target_device_id':ytdid,
            'tags':tags,
            'repo_uoa':enruoa,
            'env':env,
            'uoa':uoa,
            'deps':deps,
            'skip_auto_resolution':sar,
            'skip_default':sd,
            'local':local,
            'random':ran,
            'name':name,
            'key':ek,
            'quiet':quiet
           }
        if o=='con': ii['out']='con'
        rx=set(ii)
        if rx['return']>0: return rx

        lst=rx['lst']
        dd=rx['dict']

        dver=rx.get('detected_version','')
        if dver!='': q['detected_ver']=dver

        # add choices
        zchoices=[]
        for zw in lst:
            zchoices.append(zw['data_uid'])

        if 'choices' not in q or len('choices')==0: 
           q['choices']=zchoices

        cus=dd.get('customize',{})

        if ac=='yes': q['cus']=cus
        if sd!='yes': q['dict']=dd

        ver=cus.get('version','')
        if ver!='': q['ver']=ver

        uoa=rx['env_uoa']
        q['uoa']=uoa
        q['num_entries']=len(lst)

        if o=='con':
           ck.out('')
           x='    Resolved. CK environment UID = '+uoa
           if dver!='': x+=' (detected version '+dver+')'
           ck.out(x)

        bdn=cus.get('build_dir_name','')
        if bdn!='': q['build_dir_name']=bdn # Needed to suggest directory name for building libs

        if uoa not in res: res.append(uoa)

        env=rx['env']

        bt=rx['bat']

        q['bat']=bt
        sb+=bt

        if q.get('skip_from_bat','')!='yes':
           sb1+=bt

    if o=='con':
       ck.out('')

    return {'return':0, 'deps':deps, 'env': env, 'bat':sb, 'cut_bat':sb1, 'res_deps':res}

##############################################################################
# refresh environment (re-setup soft)

def refresh(i):
    """
    Input:  {
              (repo_uoa)          - repository UOA (with wildcards), default = local (to avoid updating other repos)
              (module_uoa)        - module UOA (with wildcards)
              (data_uoa)          - data UOA (with wildcards)

              (tags)              - prune by tags
              (target_os)         - prune by target OS
              (target_bits)       - prune by target bits
              (version)           - prune by version
              (name)              - prune by name with wildcards

              (reset_env)         - if 'yes', do not use environment from existing entry, but use original one
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              lst          - list from search function
              view         - sorted view list
            }

    """

    o=i.get('out','')

    ruoa=i.get('repo_uoa','')
    if ruoa=='': ruoa='local'

    muoa=i.get('module_uoa','')
    duoa=i.get('data_uoa','')

    tags=i.get('tags','')

    tos_uoa=i.get('target_os','')
    if tos_uoa!='':
       # Load OS
       ry=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['os'],
                     'data_uoa':tos_uoa})
       if ry['return']>0: return ry
       tos_uoa=ry['data_uoa']
       tosz=ry['dict'].get('base_uoa','')
       if tosz!='': tos_uoa=tosz
       tags+='target-os-'+tos_uoa

    tb=i.get('target_bits','')
    if tb!='':
       tags+=tb+'bits'

    ver=i.get('version','')
    if ver!='':
       tags+='v'+ver

    name=i.get('name','')
    wname=False
    if name.find('*')>=0 or name.find('?')>=0:
       import fnmatch
       wname=True 
       name=name.lower()

    ii={'action':'search',
        'module_uoa':muoa,
        'repo_uoa':ruoa,
        'data_uoa':duoa,
        'tags':tags,
        'add_info':'yes',
        'add_meta':'yes'}
    rx=ck.access(ii)
    if rx['return']>0: return rx

    lst=rx['lst']

    # prepare view
    view=[]

    lv={} # length of each field

    target_os_name={} # Caching target OS names

    for q in lst:
        vv={}

        duoa=q['data_uoa']
        duid=q['data_uid']

        ruoa=q['repo_uoa']
        ruid=q['repo_uid']

        info=q['info']
        meta=q['meta']

        cus=meta.get('customize',{})
        deps=meta.get('deps',{})
        setup=meta.get('setup','')
        tags=meta.get('tags',[])

        sftags=''
        for t in tags:
            if t!='':
               if sftags!='': sftags+=','
               sftags+=t

        host_os_uoa=setup.get('host_os_uoa','')
        target_os_uoa=setup.get('target_os_uoa','')
        tbits=setup.get('target_os_bits','')
        version=setup.get('version','')

        dname=info.get('data_name','')

        ck.out('***********************************************************************')
        ck.out(dname+' (Env: '+duid+')')

        ck.out('')
        ck.out('  Tags="'+sftags+'"')

        soft_uoa=meta.get('soft_uoa','')
        if soft_uoa=='':
           # Trying to detect by some tags
           tagsx=[]
           for q in tags:
               if not q.startswith('host-os-') and not q.startswith('target-os-') and \
                  not q.endswith('bits') and not q.startswith('v') and \
                  q!='retargeted':
                  tagsx.append(q)

           stags=''
           for t in tagsx:
               if t!='':
                  if stags!='': stags+=','
                  stags+=t

           ck.out('  All tags="'+sftags+'"')
           ck.out('  Searching soft UOA by tags="'+stags+'" ...')

           rx=ck.access({'action':'search',
                         'module_uoa':cfg['module_deps']['soft'],
                         'tags':stags})
           if rx['return']>0: return rx

           lst=rx['lst']
           if len(lst)==0:
              ck.out('')
              ck.out('  No soft found')

              rx=ck.inp({'text':'  Please, enter soft UOA: '})
              soft_uoa=rx['string'].strip()
           elif len(lst)==1:
              soft_uoa=lst[0]['data_uid']
              ck.out('     Unique soft UOA found='+lst[0]['data_uoa'])
           else:
              ck.out('')
              ck.out('  Available soft for these tags:')
              num={}
              ix=0
              for q in lst:
                  num[str(ix)]=q['data_uid']
                  ck.out('     '+str(ix)+') '+q['data_uoa'])
                  ix+=1

              rx=ck.inp({'text':'  Select one of the options for soft UOA: '})
              x=rx['string'].strip()

              if x not in num:
                 return {'return':1, 'error':'option is not recognized'}

              soft_uoa=num[x]

           meta['soft_uoa']=soft_uoa

           # Update environment entry
           rx=ck.access({'action':'update',
                         'module_uoa':work['self_module_uid'],
                         'data_uoa':duoa,
                         'dict':meta,
                         'sort_keys':'yes'})
           if rx['return']>0: return rx

        # Check if package available to take env
        penv={}
        package_uoa=meta.get('package_uoa','')
        if package_uoa!='':
           ck.out('')
           ck.out('  Related package: '+package_uoa)

           rx=ck.access({'action':'load',
                         'module_uoa':cfg['module_deps']['package'],
                         'data_uoa':package_uoa})
           if rx['return']>0: return rx
           pdd=rx['dict']
           penv=pdd.get('env',{})

        # Trying new setup
        ck.out('')
        ck.out('  Refreshing setup ...')

        ii={'action':'setup',
            'module_uoa':cfg['module_deps']['soft'],
            'host_os':host_os_uoa,
            'target_os':target_os_uoa,
            'data_uoa':soft_uoa,
            'customize':cus,
            'deps':deps,
            'tags':sftags,
            'package_uoa':package_uoa,
            'env':penv,
            'env_data_uoa':duid}
        if i.get('reset_env','')!='': ii['reset_env']=i['reset_env']
        rx=ck.access(ii)
        if rx['return']>0: 
           rrx=rx['return']
           if rrx!=32 and rrx!=33:
              return rx
           if o=='con':
              if rrx==32:
                 ck.out('')
                 ck.out('One of the dependencies is missing for this CK environment!')
              elif rrx==33:
                 ck.out('')
                 ck.out('This environment has either missing dependencies or strange mismatch between registered software environment and current setup!')

              ck.out('')
              ry=ck.inp({'text':'Would you like to delete it (Y/n)? '})
              x=ry['string'].strip().lower()
              if x!='n' and x!='no':
                 ry=ck.access({'action':'delete',
                               'module_uoa':work['self_module_uid'],
                               'data_uoa':duid})
                 if ry['return']>0: return ry
           else:
              return rx

    return {'return':0}

##############################################################################
# internal function to convert host_os and target_os from UID to UOA to be readable

def readable_os(i):
    """
    Input:  {
              setup 
                (host_os_uoa)    - UID or UOA
                (target_os_uoa)  - UID or UOA
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              setup1       - processed setup with host_os_uoa and target_os_uoa as UOA
            }
    """

    setup=i.get('setup',{})

    import copy
    setup1=copy.deepcopy(setup)

    x=setup.get('host_os_uoa','')
    if x!='':
       r=ck.access({'action':'load',
                    'module_uoa':cfg['module_deps']['os'],
                    'data_uoa':x})
       if r['return']>0: return r
       setup1['host_os_uoa']=r['data_uoa']

    x=setup.get('target_os_uoa','')
    if x!='':
       r=ck.access({'action':'load',
                    'module_uoa':cfg['module_deps']['os'],
                    'data_uoa':x})
       if r['return']>0: return r
       setup1['target_os_uoa']=r['data_uoa']

    return {'return':0, 'setup1':setup1}

##############################################################################
# internal function: get value from list without error if out of bounds

def internal_get_val(lst, index, default_value):
    v=default_value
    if index<len(lst):
       v=lst[index]
    return v
