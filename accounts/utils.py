



def detectUser(user):
    if user.role == 1:
        return 'vendorDashboard'
    elif user.role == 2:
        return 'custDashboard'
    elif user.is_superadmin:
        return '/admin'