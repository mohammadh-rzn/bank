import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {Button, Card, Input, message} from "antd";
import {EyeOutlined, EyeInvisibleOutlined} from "@ant-design/icons";
import {login, signup} from "./api-login";

const Login = () => {
    const navigate = useNavigate();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [password2, setPassword2] = useState('');
    const [isSignup, setIsSignup] = useState(false);

    const handleSubmit = async () => {
        if (!username || !password || (isSignup && !password2)) {
            message.error('Please fill in all required fields.');
            return;
        }

        if (isSignup) {
            if (password !== password2) {
                message.error("Passwords do not match.");
                return;
            }
            const response = await signup(username, password, password2, 0);
            if (response?.status === 200 || response?.status === 201) {
                message.success('Signup successful! You can now login.');
                setIsSignup(false);
                setPassword('');
                setPassword2('');
            } else {
                message.error("Signup failed. Please try again.");
            }
        } else {
            const response = await login(username, password);
            if (response?.status !== 200) {
                message.error('Username or password is incorrect.');
            } else {
                sessionStorage.setItem("access-token", response?.data?.access);
                sessionStorage.setItem("refresher-token", response?.data?.refresh);
                navigate('/dashboard/user-balance');
            }
        }
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gradient-to-r from-blue-200 to-teal-200">
            <Card
                style={{
                    width: 400,
                    padding: "30px",
                    borderRadius: "10px",
                    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                    backgroundColor: "#fff"
                }}
                bordered={false}
            >
                <div className="space-y-6">
                    <Input
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        autoComplete="off"
                        size="large"
                        className="rounded-md"
                    />
                    <Input.Password
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="off"
                        size="large"
                        iconRender={(visible) => visible ? <EyeOutlined/> : <EyeInvisibleOutlined/>}
                        className="rounded-md"
                    />
                    {isSignup && (
                        <Input.Password
                            placeholder="Repeat Password"
                            value={password2}
                            onChange={(e) => setPassword2(e.target.value)}
                            autoComplete="off"
                            size="large"
                            iconRender={(visible) => visible ? <EyeOutlined/> : <EyeInvisibleOutlined/>}
                            className="rounded-md"
                        />
                    )}
                    <Button
                        type="primary"
                        className="w-full text-lg py-5 rounded-md"
                        onClick={handleSubmit}
                        style={{
                            backgroundColor: "#1D4ED8",
                            borderColor: "#1D4ED8",
                        }}
                    >
                        {isSignup ? 'Sign Up' : 'Login'}
                    </Button>

                    <div className="text-center">
                        <span>
                            {isSignup ? "Already have an account?" : "Don't have an account?"}
                        </span>
                        <Button type="link" onClick={() => setIsSignup(!isSignup)}>
                            {isSignup ? "Login" : "Sign Up"}
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default Login;
