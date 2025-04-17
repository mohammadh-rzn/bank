import {Route, Routes} from "react-router-dom";
import Login from "../components/login/login";
import ProtectedRoute from "../config/protected-route";
import Dashboard from "../components/dashboard/dashboard";
import UserBalance from "../components/dashboard/balance/user-balance";
import Transactions from "../components/dashboard/transactions/transactions";

const ModuleRoutes = () => {
    return (
        <Routes>
            <Route
                path="/"
                element={
                    <Login/>
                }
            />
            <Route
                path="/login"
                element={
                    <Login/>
                }
            />
            <Route
                path="/dashboard/*"
                element={
                    <ProtectedRoute>
                        <Dashboard/>
                    </ProtectedRoute>
                }
            >
                <Route path="user-balance" element={<UserBalance/>}/>
                <Route path="transactions" element={<Transactions/>}/>
            </Route>
        </Routes>
    )
}

export default ModuleRoutes;