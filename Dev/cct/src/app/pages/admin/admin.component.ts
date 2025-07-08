// src/app/admin/admin.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';

import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails
} from 'amazon-cognito-identity-js';

import { environment } from "../../../../environment";

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css'],
})
export class AdminComponent implements OnInit {
  loginForm!: FormGroup;

  private userPool = new CognitoUserPool({
    UserPoolId: environment.cognito.userPoolId,
    ClientId:   environment.cognito.clientId
  });

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
      remember: [false],
    });
  }

  onLogin(): void {
    if (this.loginForm.invalid) { return; }

    const { username, password, remember } = this.loginForm.value;

    const authDetails = new AuthenticationDetails({
      Username: username,
      Password: password
    });

    const cognitoUser = new CognitoUser({
      Username: username,
      Pool:     this.userPool
    });

    cognitoUser.authenticateUser(authDetails, {
      onSuccess: (session) => {
        console.log('✔️ Login successful!', session);
        // e.g. store tokens (session.getIdToken().getJwtToken()) in localStorage if remember=true
      },
      onFailure: (err) => {
        console.error('❌ Login failed', err);
        alert(err.message || JSON.stringify(err));
      }
    });
  }
}
