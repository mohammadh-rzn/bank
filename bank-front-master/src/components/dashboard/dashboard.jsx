import {Layout, Menu, Avatar, Dropdown, Button} from 'antd';
import {UserOutlined, LogoutOutlined, TransactionOutlined, AccountBookOutlined} from '@ant-design/icons';
import {Outlet, useLocation, useNavigate} from 'react-router-dom';
import {useEffect, useState} from "react";

const {Header, Content} = Layout;

const Dashboard = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [selectedMenu, setSelectedMenu] = useState('');

    useEffect(() => {
        const path = location.pathname.split('/').pop();
        setSelectedMenu(path);
        console.log(path)
    }, [location]);

    const handleLogout = () => {
        sessionStorage.clear();
        navigate('/login');
    };

    const menu = (
        <Menu
            mode="horizontal"
            theme="dark"
        >
            <Menu.Item key="user-balance" icon={<AccountBookOutlined/>}
                       onClick={() => navigate('/dashboard/user-balance')}>
                Balance
            </Menu.Item>
            <Menu.Item icon={<LogoutOutlined/>} onClick={handleLogout}>
                Logout
            </Menu.Item>
        </Menu>
    );

    return (
        <Layout style={{minHeight: '100vh'}}>
            <Header style={{
                padding: 0,
                background: '#fff',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>

                <Menu mode="horizontal" selectedKeys={[selectedMenu]} theme="light"
                      style={{flex: 1, justifyContent: 'center'}}>
                    <Menu.Item key="user-balance" icon={<AccountBookOutlined/>}
                               onClick={() => navigate('/dashboard/user-balance')}>
                        Balance
                    </Menu.Item>
                    <Menu.Item key="transactions" icon={<TransactionOutlined/>}
                               onClick={() => navigate('/dashboard/transactions')}>
                        Transactions
                    </Menu.Item>
                </Menu>

                <div>
                    <Dropdown overlay={menu} trigger={['click']}>
                        <Button type="link">
                            <Avatar icon={<UserOutlined/>}/>
                        </Button>
                    </Dropdown>
                </div>
            </Header>

            <Outlet/>
        </Layout>
    );
};

export default Dashboard;
