#
# Collective Knowledge (individual environment - setup)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
#

##############################################################################
# setup environment setup

def setup(i):
    """
    Input:  {
              cfg              - meta of this soft entry
              self_cfg         - meta of module soft
              ck_kernel        - import CK kernel module (to reuse functions)

              host_os_uoa      - host OS UOA
              host_os_uid      - host OS UID
              host_os_dict     - host OS meta

              target_os_uoa    - target OS UOA
              target_os_uid    - target OS UID
              target_os_dict   - target OS meta

              target_device_id - target device ID (if via ADB)

              tags             - list of tags used to search this entry

              env              - updated environment vars from meta
              customize        - updated customize vars from meta

              deps             - resolved dependencies for this soft

              interactive      - if 'yes', can ask questions, otherwise quiet
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              bat          - prepared string for bat file
            }

    """

    import os

    # Get variables
    ck=i['ck_kernel']
    s=''

    iv=i.get('interactive','')

    env=i.get('env',{})
    cfg=i.get('cfg',{})
    deps=i.get('deps',{})
    tags=i.get('tags',[])
    cus=i.get('customize',{})

    host_d=i.get('host_os_dict',{})
    target_d=i.get('target_os_dict',{})
    win=target_d.get('windows_base','')
    winh=host_d.get('windows_base','')
    remote=target_d.get('remote','')
    mingw=target_d.get('mingw','')
    tbits=target_d.get('bits','')

    pi=cus.get('path_install','')

    ################################################################
    if cus.get('include_name','')=='': 
       cus['include_name']='CL/opencl.h'

    # On some Ubuntu there can be extra dir such as x86_64-linux-gnu
    # reported by Michael Kruse

    dir_extra_configured=cus.get('tool_dir_extra_configured','')
    dir_extra=cus.get('tool_dir_extra','')
    if dir_extra_configured!='yes':
       if dir_extra!='':
          ck.out('Current extra dir: '+dir_extra)
       else:
          ra=ck.inp({'text':'Enter extra directory if needed (such as x86_64-linux-gnu on Ubuntu) or Enter to skip it: '})
          dir_extra=ra['string'].strip()
          cus['tool_dir_extra_configured']='yes'

    pl=cus.get('path_lib','')
    if pl=='': 
       pl=os.path.join(pi,'lib')
       if dir_extra!='':
          pl=os.path.join(pl,dir_extra)

    if cus.get('static_lib','')=='': 
       cus['static_lib']='libOpenCL.so'
    if cus.get('dynamic_lib','')=='': 
       cus['dynamic_lib']='libOpenCL.so'

    if not os.path.isfile(os.path.join(pl,cus['dynamic_lib'])):
       return {'return':1, 'error':cus['dynamic_lib']+' is not in lib directory - please install OpenCL driver or check paths'}

    env['CK_ENV_LIB_OPENCL_INCLUDE_NAME']=cus.get('include_name','')
    env['CK_ENV_LIB_OPENCL_STATIC_NAME']=cus.get('static_lib','')
    env['CK_ENV_LIB_OPENCL_DYNAMIC_NAME']=cus.get('dynamic_lib','')

    return {'return':0, 'bat':s}
