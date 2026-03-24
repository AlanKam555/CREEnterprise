// CRE Enterprise Suite - Mobile App
// React Native with Expo

import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, FlatList, Alert, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import axios from 'axios';

// API Configuration
const API_URL = 'http://localhost:8000/api';

const Stack = createNativeStackNavigator();

// Colors
const colors = {
  dark: '#0F1419',
  surface: '#1A1F2E',
  border: '#2D3748',
  blue: '#3B82F6',
  green: '#10B981',
  red: '#EF4444',
  amber: '#F59E0B',
  white: '#FFFFFF',
  gray: '#9CA3AF',
};

// ============ API CLIENT ============
const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(config => {
  const token = global.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============ ICONS (Simple Text) ============
const Icon = ({ name, color = colors.white, size = 20 }) => {
  const icons = {
    home: '🏠',
    building: '🏢',
    dollar: '💰',
    chart: '📊',
    memo: '📝',
    plus: '➕',
    logout: '🚪',
    back: '⬅️',
    user: '👤',
  };
  return <Text style={{ fontSize: size }}>{icons[name] || '📌'}</Text>;
};

// ============ LOGIN SCREEN ============
function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/auth/login', { email, password });
      global.token = res.data.access_token;
      global.userId = res.data.user_id;
      navigation.replace('Home');
    } catch (e) {
      Alert.alert('Error', 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.loginCard}>
        <Text style={styles.logo}>🏢 CRE Suite</Text>
        <Text style={styles.subtitle}>Enterprise Edition</Text>
        
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor={colors.gray}
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor={colors.gray}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        
        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
          {loading ? (
            <ActivityIndicator color={colors.white} />
          ) : (
            <Text style={styles.buttonText}>Login</Text>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.linkButton}>
          <Text style={styles.linkText}>Don't have an account? Sign up</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ============ HOME SCREEN ============
function HomeScreen({ navigation }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get('/dashboard');
      setStats(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <Text style={styles.headerSubtitle}>Welcome back!</Text>
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats?.total_properties || 0}</Text>
          <Text style={styles.statLabel}>Properties</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats?.total_valuations || 0}</Text>
          <Text style={styles.statLabel}>Valuations</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: colors.green }]}>{stats?.avg_irr || 0}%</Text>
          <Text style={styles.statLabel}>Avg IRR</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: colors.amber }]}>{stats?.avg_dscr || 0}</Text>
          <Text style={styles.statLabel}>Avg DSCR</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Quick Actions</Text>
      
      <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('Properties')}>
        <Icon name="building" size={24} />
        <Text style={styles.menuText}>Properties</Text>
        <Text style={styles.menuArrow}>›</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('Valuations')}>
        <Icon name="dollar" size={24} />
        <Text style={styles.menuText}>Valuations</Text>
        <Text style={styles.menuArrow}>›</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('RentRoll')}>
        <Icon name="chart" size={24} />
        <Text style={styles.menuText}>Rent Roll</Text>
        <Text style={styles.menuArrow}>›</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('Memos')}>
        <Icon name="memo" size={24} />
        <Text style={styles.menuText}>Memos</Text>
        <Text style={styles.menuArrow}>›</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutButton} onPress={() => navigation.replace('Login')}>
        <Icon name="logout" size={20} />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// ============ PROPERTIES SCREEN ============
function PropertiesScreen({ navigation }) {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', asset_type: 'multifamily', address: '', purchase_price: '' });

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    setLoading(true);
    try {
      const res = await api.get('/properties');
      setProperties(res.data.properties || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.name || !form.address) {
      Alert.alert('Error', 'Please fill in required fields');
      return;
    }
    try {
      await api.post('/properties', form);
      setForm({ name: '', asset_type: 'multifamily', address: '', purchase_price: '' });
      setShowForm(false);
      loadProperties();
    } catch (e) {
      Alert.alert('Error', 'Failed to create property');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.screenHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="back" size={24} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Properties</Text>
        <TouchableOpacity onPress={() => setShowForm(!showForm)}>
          <Icon name="plus" size={24} color={colors.blue} />
        </TouchableOpacity>
      </View>

      {showForm && (
        <View style={styles.formCard}>
          <TextInput style={styles.input} placeholder="Property Name" placeholderTextColor={colors.gray} value={form.name} onChangeText={t => setForm({ ...form, name: t })} />
          <TextInput style={styles.input} placeholder="Address" placeholderTextColor={colors.gray} value={form.address} onChangeText={t => setForm({ ...form, address: t })} />
          <TextInput style={styles.input} placeholder="Purchase Price" placeholderTextColor={colors.gray} value={form.purchase_price} onChangeText={t => setForm({ ...form, purchase_price: t })} keyboardType="numeric" />
          <TouchableOpacity style={styles.button} onPress={handleCreate}>
            <Text style={styles.buttonText}>Create Property</Text>
          </TouchableOpacity>
        </View>
      )}

      {loading ? (
        <ActivityIndicator size="large" color={colors.blue} />
      ) : (
        <FlatList
          data={properties}
          keyExtractor={item => item.id}
          renderItem={({ item }) => (
            <View style={styles.propertyCard}>
              <Text style={styles.propertyName}>{item.name}</Text>
              <Text style={styles.propertyType}>{item.asset_type}</Text>
              <Text style={styles.propertyAddress}>{item.address}</Text>
              <Text style={styles.propertyPrice}>${parseFloat(item.purchase_price || 0).toLocaleString()}</Text>
            </View>
          )}
          ListEmptyComponent={<Text style={styles.emptyText}>No properties yet</Text>}
        />
      )}
    </View>
  );
}

// ============ VALUATIONS SCREEN ============
function ValuationsScreen({ navigation }) {
  const [properties, setProperties] = useState([]);
  const [selectedProp, setSelectedProp] = useState(null);
  const [form, setForm] = useState({ noi: '', cap_rate: '5', debt_service: '', equity_invested: '' });
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    try {
      const res = await api.get('/properties');
      setProperties(res.data.properties || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCalculate = async () => {
    if (!selectedProp || !form.noi) {
      Alert.alert('Error', 'Please select property and enter NOI');
      return;
    }
    try {
      const res = await api.post('/valuations', {
        property_id: selectedProp,
        valuation_type: 'standard',
        noi: parseFloat(form.noi),
        cap_rate: parseFloat(form.cap_rate) || 5,
        debt_service: parseFloat(form.debt_service) || 0,
        equity_invested: parseFloat(form.equity_invested) || 0
      });
      setResult(res.data.valuation);
    } catch (e) {
      Alert.alert('Error', 'Failed to calculate');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.screenHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="back" size={24} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Valuations</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.formCard}>
        <Text style={styles.label}>Select Property</Text>
        <View style={styles.picker}>
          {properties.map(p => (
            <TouchableOpacity key={p.id} style={[styles.pickerItem, selectedProp === p.id && styles.pickerItemSelected]} onPress={() => setSelectedProp(p.id)}>
              <Text style={[styles.pickerText, selectedProp === p.id && styles.pickerTextSelected]}>{p.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TextInput style={styles.input} placeholder="NOI ($)" placeholderTextColor={colors.gray} value={form.noi} onChangeText={t => setForm({ ...form, noi: t })} keyboardType="numeric" />
        <TextInput style={styles.input} placeholder="Cap Rate (%)" placeholderTextColor={colors.gray} value={form.cap_rate} onChangeText={t => setForm({ ...form, cap_rate: t })} keyboardType="numeric" />
        <TextInput style={styles.input} placeholder="Debt Service ($)" placeholderTextColor={colors.gray} value={form.debt_service} onChangeText={t => setForm({ ...form, debt_service: t })} keyboardType="numeric" />
        <TextInput style={styles.input} placeholder="Equity Invested ($)" placeholderTextColor={colors.gray} value={form.equity_invested} onChangeText={t => setForm({ ...form, equity_invested: t })} keyboardType="numeric" />
        
        <TouchableOpacity style={styles.button} onPress={handleCalculate}>
          <Text style={styles.buttonText}>Calculate</Text>
        </TouchableOpacity>
      </View>

      {result && (
        <View style={styles.resultCard}>
          <Text style={styles.resultTitle}>Results</Text>
          <View style={styles.resultGrid}>
            <View style={styles.resultItem}>
              <Text style={styles.resultValue}>{result.irr}%</Text>
              <Text style={styles.resultLabel}>IRR</Text>
            </View>
            <View style={styles.resultItem}>
              <Text style={styles.resultValue}>{result.coc}%</Text>
              <Text style={styles.resultLabel}>CoC</Text>
            </View>
            <View style={styles.resultItem}>
              <Text style={styles.resultValue}>{result.dscr}</Text>
              <Text style={styles.resultLabel}>DSCR</Text>
            </View>
            <View style={styles.resultItem}>
              <Text style={styles.resultValue}>{result.cap_rate}%</Text>
              <Text style={styles.resultLabel}>Cap Rate</Text>
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

// ============ RENT ROLL SCREEN ============
function RentRollScreen({ navigation }) {
  const [properties, setProperties] = useState([]);
  const [selectedProp, setSelectedProp] = useState(null);
  const [rentRoll, setRentRoll] = useState(null);

  useEffect(() => {
    loadProperties();
  }, []);

  useEffect(() => {
    if (selectedProp) loadRentRoll();
  }, [selectedProp]);

  const loadProperties = async () => {
    try {
      const res = await api.get('/properties');
      setProperties(res.data.properties || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadRentRoll = async () => {
    try {
      const res = await api.get(`/properties/${selectedProp}/rent-roll`);
      setRentRoll(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.screenHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="back" size={24} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Rent Roll</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.formCard}>
        <Text style={styles.label}>Select Property</Text>
        <View style={styles.picker}>
          {properties.map(p => (
            <TouchableOpacity key={p.id} style={[styles.pickerItem, selectedProp === p.id && styles.pickerItemSelected]} onPress={() => setSelectedProp(p.id)}>
              <Text style={[styles.pickerText, selectedProp === p.id && styles.pickerTextSelected]}>{p.name}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {rentRoll && (
        <View style={styles.resultCard}>
          <Text style={styles.resultTitle}>Summary</Text>
          <View style={styles.resultGrid}>
            <View style={styles.resultItem}>
              <Text style={styles.resultValue}>{rentRoll.total_units}</Text>
              <Text style={styles.resultLabel}>Units</Text>
            </View>
            <View style={styles.resultItem}>
              <Text style={[styles.resultValue, { color: colors.green }]}>{rentRoll.occupied_units}</Text>
              <Text style={styles.resultLabel}>Occupied</Text>
            </View>
            <View style={styles.resultItem}>
              <Text style={[styles.resultValue, { color: colors.amber }]}>{rentRoll.occupancy_rate}%</Text>
              <Text style={styles.resultLabel}>Occupancy</Text>
            </View>
            <View style={styles.resultItem}>
              <Text style={styles.resultValue}>${(rentRoll.total_monthly_rent / 1000).toFixed(1)}K</Text>
              <Text style={styles.resultLabel}>Monthly</Text>
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

// ============ MEMOS SCREEN ============
function MemosScreen({ navigation }) {
  const [properties, setProperties] = useState([]);
  const [selectedProp, setSelectedProp] = useState(null);
  const [memo, setMemo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    try {
      const res = await api.get('/properties');
      setProperties(res.data.properties || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerate = async () => {
    if (!selectedProp) {
      Alert.alert('Error', 'Please select a property');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post(`/properties/${selectedProp}/memo`, {
        title: 'Investment Memo',
        memo_type: 'investment'
      });
      setMemo(res.data.memo);
    } catch (e) {
      Alert.alert('Error', 'Failed to generate memo');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.screenHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="back" size={24} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Investor Memos</Text>
        <View style={{ width: 24 }} />
      </View>

      <View style={styles.formCard}>
        <Text style={styles.label}>Select Property</Text>
        <View style={styles.picker}>
          {properties.map(p => (
            <TouchableOpacity key={p.id} style={[styles.pickerItem, selectedProp === p.id && styles.pickerItemSelected]} onPress={() => setSelectedProp(p.id)}>
              <Text style={[styles.pickerText, selectedProp === p.id && styles.pickerTextSelected]}>{p.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.button} onPress={handleGenerate} disabled={loading}>
          {loading ? (
            <ActivityIndicator color={colors.white} />
          ) : (
            <Text style={styles.buttonText}>Generate Memo</Text>
          )}
        </TouchableOpacity>
      </View>

      {memo && (
        <View style={styles.memoCard}>
          <Text style={styles.memoText}>{memo}</Text>
        </View>
      )}
    </ScrollView>
  );
}

// ============ MAIN APP ============
export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Properties" component={PropertiesScreen} />
        <Stack.Screen name="Valuations" component={ValuationsScreen} />
        <Stack.Screen name="RentRoll" component={RentRollScreen} />
        <Stack.Screen name="Memos" component={MemosScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

// ============ STYLES ============
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.dark,
    padding: 16,
  },
  // Login
  loginCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 24,
    marginTop: 100,
  },
  logo: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: colors.gray,
    textAlign: 'center',
    marginBottom: 24,
  },
  input: {
    backgroundColor: colors.dark,
    borderRadius: 8,
    padding: 12,
    color: colors.white,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  button: {
    backgroundColor: colors.blue,
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: colors.white,
    fontWeight: 'bold',
    fontSize: 16,
  },
  linkButton: {
    marginTop: 16,
    alignItems: 'center',
  },
  linkText: {
    color: colors.blue,
    fontSize: 14,
  },
  // Home
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.white,
  },
  headerSubtitle: {
    fontSize: 14,
    color: colors.gray,
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  statCard: {
    width: '48%',
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.blue,
  },
  statLabel: {
    fontSize: 12,
    color: colors.gray,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.white,
    marginBottom: 12,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  menuText: {
    flex: 1,
    color: colors.white,
    fontSize: 16,
    marginLeft: 12,
  },
  menuArrow: {
    color: colors.gray,
    fontSize: 20,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.red + '20',
    borderRadius: 12,
    padding: 14,
    marginTop: 24,
  },
  logoutText: {
    color: colors.red,
    fontSize: 16,
    marginLeft: 8,
  },
  // Screen Header
  screenHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.white,
  },
  // Form
  formCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  label: {
    color: colors.gray,
    fontSize: 12,
    marginBottom: 8,
  },
  picker: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  pickerItem: {
    backgroundColor: colors.dark,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginRight: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pickerItemSelected: {
    backgroundColor: colors.blue,
    borderColor: colors.blue,
  },
  pickerText: {
    color: colors.gray,
  },
  pickerTextSelected: {
    color: colors.white,
  },
  // Results
  resultCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.white,
    marginBottom: 16,
  },
  resultGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  resultItem: {
    width: '48%',
    backgroundColor: colors.dark,
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    alignItems: 'center',
  },
  resultValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.blue,
  },
  resultLabel: {
    fontSize: 12,
    color: colors.gray,
    marginTop: 4,
  },
  // Properties
  propertyCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  propertyName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.white,
  },
  propertyType: {
    fontSize: 14,
    color: colors.blue,
    marginTop: 4,
  },
  propertyAddress: {
    fontSize: 12,
    color: colors.gray,
    marginTop: 4,
  },
  propertyPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.green,
    marginTop: 8,
  },
  emptyText: {
    color: colors.gray,
    textAlign: 'center',
    marginTop: 40,
  },
  // Memo
  memoCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
  },
  memoText: {
    color: colors.gray,
    fontSize: 12,
    fontFamily: 'monospace',
  },
});
